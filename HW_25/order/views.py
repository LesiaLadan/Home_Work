from decimal import Decimal, ROUND_HALF_UP

import structlog
import stripe
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import F
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from asgiref.sync import sync_to_async
from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme
from order.tasks import send_order_confirmation_email
from shop.models import Book
from user_management.models import DeliveryAddress, User
from .forms import DeliveryAddressForm
from .models import Order, OrderDetails, PaymentStatus, OrderStatus, PaymentMethod
from .cart import Cart

stripe.api_key = settings.STRIPE_SECRET_KEY
client = stripe.StripeClient(settings.STRIPE_SECRET_KEY)

logger = structlog.get_logger(__name__)


class InsufficientStockError(Exception):
    """Raised when a book no longer has enough stock to fulfil an order line.

    Used to abort and roll back the ``PlaceOrderView`` transaction when the
    authoritative, race-safe stock update (see ``PlaceOrderView.post``) fails
    because another request consumed the remaining stock first.
    """

    def __init__(self, book_title: str, available: int):
        self.book_title = book_title
        self.available = available
        super().__init__(f'Only {available} copies of "{book_title}" are available.')


def get_price_for_user(book: Book, user: User) -> Decimal:
    """Return the price that applies to ``user`` for ``book``.

    Wholesale price is used only when the user has the
    ``shop.view_wholesale_price`` permission *and* the book actually has a
    wholesale price configured; otherwise the regular retail price is used.
    Centralized here because the same calculation is needed by the cart,
    checkout, and order-placement views.
    """
    if user.has_perm("shop.view_wholesale_price") and book.wholesale_price is not None:
        return book.wholesale_price
    return book.price


class AddToCartView(LoginRequiredMixin, View):
    """Add a single book to the current user's session cart and redirect back."""

    def post(self, request: HttpRequest, book_id: int) -> HttpResponse:
        Cart(request).add(book_id)

        next_url = request.POST.get("next")

        if next_url and url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            return redirect(next_url)

        return redirect("order:cart")


class CartView(LoginRequiredMixin, TemplateView):
    """Display the contents of the current user's cart with computed totals."""

    template_name = "order/cart.html"

    def get_context_data(self, **kwargs):
        """Build cart line items (book, quantity, price, subtotal) and the cart total."""
        context = super().get_context_data(**kwargs)

        cart = Cart(self.request)
        cart_data = []
        total = Decimal("0")

        for book in cart.get_books():
            price = get_price_for_user(book, self.request.user)
            quantity = cart.get_quantity(book.pk)
            subtotal = quantity * price

            cart_data.append(
                {
                    "book": book,
                    "quantity": quantity,
                    "price": price,
                    "subtotal": subtotal,
                }
            )

            total += subtotal

        context["cart_data"] = cart_data
        context["total"] = total

        cart.set_total(total)

        return context


class RemoveFromCartView(LoginRequiredMixin, View):
    """Remove a single book from the current user's session cart."""

    def post(self, request: HttpRequest, book_id: int) -> HttpResponse:
        Cart(request).remove(book_id)
        return redirect("order:cart")


class CheckoutView(LoginRequiredMixin, TemplateView):
    """Show the checkout page: cart review, delivery address form, and totals."""

    template_name = "order/checkout.html"

    def get_context_data(self, **kwargs):
        """Recompute checkout totals, warn on price drift, and pre-fill the address form."""
        context = super().get_context_data(**kwargs)
        cart = Cart(self.request)
        books = cart.get_books()
        checkout_data = []
        total = Decimal("0")

        for book in books:
            price = get_price_for_user(book, self.request.user)
            quantity = cart.get_quantity(book.pk)
            subtotal = quantity * price

            checkout_data.append(
                {
                    "book": book,
                    "price": price,
                    "quantity": quantity,
                    "subtotal": subtotal,
                }
            )

            total += subtotal

        previous_total = cart.get_total()

        if previous_total != total:
            messages.warning(
                self.request,
                "One or more book prices have changed. " "Please review your order.",
            )

        last_address = (
            DeliveryAddress.objects.filter(owner=self.request.user)
            .order_by("-id")
            .first()
        )

        if last_address:
            form = DeliveryAddressForm(instance=last_address)
        else:
            form = DeliveryAddressForm()

        context["checkout_data"] = checkout_data
        context["total"] = total
        context["form"] = form

        return context


class PlaceOrderView(LoginRequiredMixin, View):
    """Validate the delivery address and cart, then create the order and its details.

    On success this creates (or reuses) a ``DeliveryAddress``, an ``Order``,
    one ``OrderDetails`` row per cart line, decrements book stock, sends a
    confirmation email, clears the cart, and redirects either to Stripe
    checkout (card payment) or straight to the order-success page (cash).
    """

    def post(self, request: HttpRequest) -> HttpResponse:
        """Handle order submission.

        Validates the delivery address form and the cart contents (not
        empty, no items removed since checkout was rendered, enough stock
        for every line), then atomically creates the order. Stock is
        decremented with a conditional ``UPDATE ... WHERE in_stock >=
        quantity`` inside the transaction so a race between two concurrent
        checkouts for the same book cannot oversell it; if that safety
        check fails the whole transaction is rolled back and the user is
        redirected back to their cart with an explanation.
        """
        form = DeliveryAddressForm(request.POST)

        if not form.is_valid():
            return render(
                request,
                "order/checkout.html",
                {
                    "form": form,
                },
            )

        cart = Cart(request)

        if cart.is_empty():
            messages.warning(request, "Your cart is empty")
            return redirect("order:cart")

        books = cart.get_books()

        cart_book_ids = set(cart.cart.keys())
        found_book_ids = {str(book.pk) for book in books}
        missing_book_ids = cart_book_ids - found_book_ids

        if missing_book_ids:
            messages.warning(
                request,
                "Some items in your cart are no longer available. Please review your cart.",
            )
            logger.warning(
                "Cart references missing books at checkout",
                missing_book_ids=list(missing_book_ids),
                user=request.user.username,
            )
            return redirect("order:cart")

        data = form.cleaned_data
        total = Decimal("0")
        order_items = []

        for book in books:
            price = get_price_for_user(book, request.user)
            quantity = cart.get_quantity(book.pk)

            if book.in_stock < quantity:
                messages.error(
                    request,
                    f'Only {book.in_stock} copies of "{book.title}" are available.',
                )
                return redirect("order:cart")

            total += price * quantity

            order_items.append(
                {
                    "book": book,
                    "quantity": quantity,
                    "price": price,
                }
            )

        if not order_items:
            messages.warning(request, "Your cart is empty")
            return redirect("order:cart")

        try:
            with transaction.atomic():
                address, _ = DeliveryAddress.objects.get_or_create(
                    owner=request.user,
                    postal_code=data["postal_code"],
                    city=data["city"],
                    street=data["street"],
                    branch=data["branch"],
                )

                order = Order.objects.create(
                    owner=request.user,
                    delivery_address=address,
                    total_price=total,
                    payment_method=data["payment_method"],
                    payment_status=PaymentStatus.PENDING.value,
                    status=OrderStatus.PENDING.value,
                )

                for item in order_items:
                    OrderDetails.objects.create(
                        order=order,
                        book=item["book"],
                        quantity=item["quantity"],
                        price=item["price"],
                    )

                    updated_rows = Book.objects.filter(
                        pk=item["book"].pk,
                        in_stock__gte=item["quantity"],
                    ).update(in_stock=F("in_stock") - item["quantity"])

                    if not updated_rows:
                        raise InsufficientStockError(
                            item["book"].title, item["book"].in_stock
                        )

                cart.clear()
        except InsufficientStockError as exc:
            messages.error(request, str(exc))
            logger.warning(
                "Order placement failed due to insufficient stock",
                book=exc.book_title,
                available=exc.available,
                user=request.user.username,
            )
            return redirect("order:cart")

        logger.info(
            "Order created",
            order_id=order.pk,
            user=request.user.username,
            total_price=str(order.total_price),
            payment_method=order.payment_method,
        )

        user_name = request.user.first_name or request.user.username

        try:
            send_order_confirmation_email.delay(
                order.pk,
                user_name,
                request.user.email,
                str(order.total_price),
                order.payment_method,
            )
        except Exception:
            logger.exception(
                "Failed to send order confirmation email", order_id=order.pk
            )

        if order.payment_method == PaymentMethod.CARD.value:
            return redirect("order:stripe", order_id=order.pk)

        return redirect("order:order_success")


class OrderSuccessView(LoginRequiredMixin, TemplateView):
    """Show the order-success page after a completed checkout or Stripe redirect."""

    template_name = "order/order_success.html"

    def get_context_data(self, **kwargs):
        """Pass through the Stripe checkout session id, if present, for display."""
        context = super().get_context_data(**kwargs)

        context["checkout_session_id"] = self.kwargs.get("checkout_session_id")

        return context


async def create_checkout_session(request: HttpRequest, order_id: int) -> HttpResponse:
    """Create a Stripe Checkout session for ``order_id`` and redirect the user to it.

    Args:
        request: The current request; must belong to an authenticated user
            who owns the order.
        order_id: Primary key of the ``Order`` to pay for.

    Returns:
        A redirect to the Stripe-hosted checkout page on success, or back to
        the checkout page with a flashed error message on failure (order not
        found/not owned by the user, or a Stripe API error).
    """
    if not request.user.is_authenticated:
        return redirect("user_management:login")

    try:
        order = await Order.objects.aget(pk=order_id, owner=request.user)
    except Order.DoesNotExist:
        await sync_to_async(messages.error)(request, "Order not found.")
        return redirect("order:checkout")

    unit_amount = int(
        (order.total_price * 100).to_integral_value(rounding=ROUND_HALF_UP)
    )

    try:
        session = await sync_to_async(stripe.checkout.Session.create)(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": "Book order",
                        },
                        "unit_amount": unit_amount,
                    },
                    "quantity": 1,
                },
            ],
            mode="payment",
            metadata={"order_id": str(order.pk)},
            success_url="http://localhost:8000/orders/success/?checkout_session_id={CHECKOUT_SESSION_ID}",
            cancel_url="http://localhost:8000/order_error/?error=epayment_error",
        )
        if not session.url:
            raise ValueError("Stripe checkout session URL is missing")
    except stripe.StripeError as exc:
        logger.warning(
            "Stripe error while creating checkout session",
            order_id=order.pk,
            error=str(exc),
        )
        await sync_to_async(messages.error)(
            request, f"Error creating Stripe checkout session: {exc}"
        )
        return redirect("order:checkout")
    except Exception:
        logger.exception(
            "Unexpected error while creating Stripe checkout session",
            order_id=order.pk,
        )
        await sync_to_async(messages.error)(
            request, "Error creating Stripe checkout session. Please try again."
        )
        return redirect("order:checkout")

    logger.info(
        "Stripe checkout session created",
        order_id=order.pk,
        session_id=session.id,
    )
    return redirect(session.url)


@csrf_exempt
async def stripe_webhook(request: HttpRequest) -> HttpResponse:
    """Handle a Stripe webhook event.

    Exempt from CSRF protection because Stripe cannot supply a Django CSRF
    token; the request is instead authenticated by verifying the Stripe
    signature below (``stripe.Webhook.construct_event``), which must always
    run before any data from the payload is trusted.

    Currently handles ``checkout.session.completed`` by marking the
    matching ``Order`` as paid. Processing is idempotent: if the order is
    already ``COMPLETED`` the event is treated as a duplicate delivery (which
    Stripe explicitly documents as possible) and skipped without error.

    Returns:
        ``HttpResponse`` with status 400 for an invalid/unverifiable payload
        or missing order metadata, 404 if the referenced order does not
        exist, and 200 otherwise (including for skipped duplicates), since a
        non-2xx response causes Stripe to retry delivery.
    """
    payload = request.body
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError as exc:
        if not settings.STRIPE_WEBHOOK_SECRET:
            logger.error(
                "Stripe webhook secret is not configured", error=str(exc)
            )
        else:
            logger.warning(
                "Stripe webhook signature verification failed", error=str(exc)
            )
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        order_id = session.get("metadata", {}).get("order_id")

        if not order_id:
            logger.warning(
                "Stripe checkout.session.completed event missing order_id metadata",
                event_id=event.get("id"),
            )
            return HttpResponse(status=400)

        try:
            order = await Order.objects.aget(pk=order_id)
        except Order.DoesNotExist:
            logger.warning(
                "Stripe webhook references unknown order",
                order_id=order_id,
                event_id=event.get("id"),
            )
            return HttpResponse(status=404)

        if order.payment_status == PaymentStatus.COMPLETED.value:
            logger.info(
                "Duplicate Stripe webhook delivery skipped, order already completed",
                order_id=order.pk,
                event_id=event.get("id"),
            )
            return HttpResponse(status=200)

        order.payment_status = PaymentStatus.COMPLETED.value
        await order.asave(update_fields=["payment_status"])
        logger.info(
            "Order marked as paid via Stripe webhook",
            order_id=order.pk,
            event_id=event.get("id"),
        )

    return HttpResponse(status=200)
