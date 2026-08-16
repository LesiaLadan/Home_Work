from django.db.models import F
from django.shortcuts import redirect, get_object_or_404, render
from django.views.generic import TemplateView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db import transaction
from psycopg import logger
from shop.models import Book
from user_management.models import DeliveryAddress
from .forms import DeliveryAddressForm
from .models import Order, OrderDetails, PaymentStatus, OrderStatus, PaymentMethod
import stripe
# from book_store import settings
from .cart import Cart
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.core.mail import send_mail
from asgiref.sync import sync_to_async
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY
client = stripe.StripeClient(settings.STRIPE_SECRET_KEY)


class AddToCartView(LoginRequiredMixin, View):

    def post(self, request, book_id):
        Cart(request).add(book_id)

        return redirect(request.POST.get("next", "order:cart"))


class CartView(LoginRequiredMixin, TemplateView):
    template_name = "order/cart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cart = Cart(self.request)
        cart_data = []
        total = 0

        for book in cart.get_books():

            if self.request.user.has_perm("shop.view_wholesale_price"):
                price = book.wholesale_price
            else:
                price = book.price

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

    def post(self, request, book_id):
        Cart(request).remove(book_id)
        return redirect("order:cart")


class CheckoutView(LoginRequiredMixin, TemplateView):
    template_name = "order/checkout.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = Cart(self.request)
        books = cart.get_books()
        checkout_data = []
        total = 0

        for book in books:
            if self.request.user.has_perm("shop.view_wholesale_price"):
                price = book.wholesale_price
            else:
                price = book.price

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

    def post(self, request):

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

        with transaction.atomic():

            data = form.cleaned_data

            address = DeliveryAddress.objects.filter(
                owner=request.user,
                postal_code=data["postal_code"],
                city=data["city"],
                street=data["street"],
                branch=data["branch"],
            ).first()

            if address is None:
                address = DeliveryAddress.objects.create(
                    owner=request.user,
                    postal_code=data["postal_code"],
                    city=data["city"],
                    street=data["street"],
                    branch=data["branch"],
                )

            total = 0
            order_items = []

            for book in books:

                if request.user.has_perm("shop.view_wholesale_price"):
                    price = book.wholesale_price
                else:
                    price = book.price

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

                Book.objects.filter(pk=item["book"].pk).update(
                    in_stock=F("in_stock") - item["quantity"]
                )

            user_name = request.user.first_name or request.user.username

            send_mail(
                subject=f"Order #{order.pk} created",
                message=(
                    f"Hello, {user_name}!\n\n"
                    f"Thank you for your order.\n\n"
                    f"Order number: {order.pk}\n"
                    f"Total amount: {order.total_price} UAH\n"
                    f"Payment method: {order.payment_method}\n\n"
                    f"We will notify you when your order is processed."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[request.user.email],
                fail_silently=False,
            )

            cart.clear()

            if order.payment_method == PaymentMethod.CARD.value:
                return redirect("order:stripe", order_id=order.pk)

        return redirect("order:order_success")


class OrderSuccessView(LoginRequiredMixin, TemplateView):
    template_name = "order/order_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["checkout_session_id"] = self.kwargs.get("checkout_session_id")

        return context


async def create_checkout_session(request, order_id):
    try:
        order = await Order.objects.aget(pk=order_id, owner=request.user)
        session = await sync_to_async(stripe.checkout.Session.create)(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": "Book order",
                        },
                        "unit_amount": int(order.total_price * 100),
                    },
                    "quantity": 1,
                },
            ],
            mode="payment",
            metadata={"order_id": str(order.pk)},
            # success_url="http://localhost:8000/orders/success/{CHECKOUT_SESSION_ID}/",
            success_url="http://localhost:8000/orders/success/?checkout_session_id={CHECKOUT_SESSION_ID}",
            cancel_url="http://localhost:8000/order_error/?error=epayment_error",
        )
        if not session.url:
            raise ValueError("Stripe checkout session URL is missing")
        logger.info(
            "Stripe checkout session created",
            order_id=order.pk,
            session_id=session.id,
        )
        return redirect(session.url)

    except Exception as e:
        await sync_to_async(messages.error)(
            request, f"Error creating Stripe checkout session: {str(e)}"
            )
        return redirect("order:checkout")


@csrf_exempt
async def stripe_webhook(request):
    payload = request.body
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        order_id = session["metadata"]["order_id"]

        try:
            order = await Order.objects.aget(pk=order_id)

            order.payment_status = PaymentStatus.COMPLETED.value
            await order.asave(update_fields=["payment_status"])

        except Order.DoesNotExist:
            return HttpResponse(status=404)

    return HttpResponse(status=200)
