import enum

from django.db import models
from django.utils.translation import gettext_lazy

from book_store import settings


class OrderDetails(models.Model):
    order = models.ForeignKey(
        "Order",
        on_delete=models.CASCADE,
        related_name="order_details",
        verbose_name=gettext_lazy("Order"),
    )
    book = models.ForeignKey(
        "shop.Book",
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy("Book"),
    )
    quantity = models.PositiveIntegerField(
        gettext_lazy("Quantity"),
    )
    price = models.DecimalField(
        gettext_lazy("Price"),
        max_digits=6,
        decimal_places=2,
    )

    def __str__(self):
        return f"{self.book.title}, {self.order.id}, {self.quantity}"


class PaymentMethod(enum.Enum):
    CASH = "cash"
    CARD = "card"


class PaymentStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class OrderStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELED = "canceled"


class Order(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name=gettext_lazy("Owner"),
    )

    delivery_address = models.ForeignKey(
        "user_management.DeliveryAddress",
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy("Delivery address"),
    )

    order_date = models.DateTimeField(
        gettext_lazy("Order date"),
        auto_now_add=True,
    )

    status = models.CharField(
        gettext_lazy("Status"),
        max_length=20,
        choices=[(item.value, item.name.title()) for item in OrderStatus],
        default=OrderStatus.PENDING.value,
    )

    total_price = models.DecimalField(
        gettext_lazy("Total price"),
        max_digits=8,
        decimal_places=2,
    )

    payment_method = models.CharField(
        gettext_lazy("Payment method"),
        max_length=20,
        choices=[(item.value, item.name.title()) for item in PaymentMethod],
        default=PaymentMethod.CASH.value,
    )

    payment_status = models.CharField(
        gettext_lazy("Payment status"),
        max_length=20,
        choices=[(item.value, item.name.title()) for item in PaymentStatus],
        default=PaymentStatus.PENDING.value,
    )

    ttn = models.CharField(
        gettext_lazy("TTN"),
        max_length=100,
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"Order {self.pk}"