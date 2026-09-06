import django_filters

from order.models import Order
from shop.models import Book


class BookFilter(django_filters.FilterSet):
    price_min = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    category = django_filters.NumberFilter(field_name="category__id")
    author = django_filters.NumberFilter(field_name="author__id")

    class Meta:
        model = Book
        fields = [
            "category",
            "author",
            "language",
            "in_stock",
            "price_min",
            "price_max",
        ]


class OrderFilter(django_filters.FilterSet):
    order_date_after = django_filters.DateFilter(
        field_name="order_date", lookup_expr="gte"
    )
    order_date_before = django_filters.DateFilter(
        field_name="order_date", lookup_expr="lte"
    )

    class Meta:
        model = Order
        fields = ["status", "payment_status", "order_date_after", "order_date_before"]
