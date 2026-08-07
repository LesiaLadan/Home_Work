import enum

from django.db import models

from book_store import settings


class OrderDetails(models.Model):
    order = models.ForeignKey(
        "Order", on_delete=models.CASCADE, related_name="order_details"
    )
    book = models.ForeignKey("shop.Book", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=6, decimal_places=2)

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
    )

    delivery_address = models.ForeignKey(
        "user_management.DeliveryAddress", on_delete=models.CASCADE
    )
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[(item.value, item.name.title()) for item in OrderStatus],
        default=OrderStatus.PENDING.value,
    )
    total_price = models.DecimalField(max_digits=8, decimal_places=2)
    payment_method = models.CharField(
        max_length=20,
        choices=[(item.value, item.name.title()) for item in PaymentMethod],
        default=PaymentMethod.CASH.value,
    )
    payment_status = models.CharField(
        max_length=20,
        choices=[(item.value, item.name.title()) for item in PaymentStatus],
        default=PaymentStatus.PENDING.value,
    )
    ttn = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Order {self.pk}"
