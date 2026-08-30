from rest_framework import mixins, status, viewsets
from rest_framework.decorators import APIView, action
from rest_framework.permissions import (
    IsAdminUser,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from order.cart import Cart
from order.models import Order
from shop.models import Book, Category

from .filters import BookFilter, OrderFilter
from .permissions import IsOwnerOrReadOnly
from .serializers import (
    BookSerializer,
    CartAddSerializer,
    CartSerializer,
    CategorySerializer,
    OrderSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdminUser()]
        return super().get_permissions()


class BookViewSet(viewsets.ModelViewSet):
    queryset = (
        Book.objects.all()
        .prefetch_related("author", "category")
        .select_related("publisher")
        .order_by("id")
    )
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_class = BookFilter

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdminUser()]
        return super().get_permissions()


class OrderViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    filterset_class = OrderFilter

    def get_queryset(self):
        return (
            Order.objects.filter(owner=self.request.user)
            .select_related("delivery_address")
            .prefetch_related("order_details__book")
            .order_by("-order_date")
        )


def cart_data(request):
    cart = Cart(request)
    items = []
    total = 0

    for book in cart.get_books():
        if (
            request.user.has_perm("shop.view_wholesale_price")
            and book.wholesale_price
        ):
            price = book.wholesale_price
        else:
            price = book.price

        quantity = cart.get_quantity(book.pk)
        subtotal = price * quantity
        total += subtotal

        items.append(
            {
                "book_id": book.pk,
                "title": book.title,
                "price": price,
                "quantity": quantity,
                "subtotal": subtotal,
            }
        )

    cart.set_total(total)
    return {"items": items, "total": total}


class CartMixin:
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "cart"


class CartView(CartMixin, APIView):
    def get(self, request):
        return Response(CartSerializer(cart_data(request)).data)


class CartAddView(CartMixin, APIView):
    def post(self, request):
        serializer = CartAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        Cart(request).add(serializer.validated_data["book_id"])
        return Response(CartSerializer(cart_data(request)).data)


class CartRemoveView(CartMixin, APIView):
    def post(self, request):
        serializer = CartAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        Cart(request).remove(serializer.validated_data["book_id"])
        return Response(CartSerializer(cart_data(request)).data)


class CartClearView(CartMixin, APIView):
    def post(self, request):
        Cart(request).clear()
        return Response(status=status.HTTP_204_NO_CONTENT)
