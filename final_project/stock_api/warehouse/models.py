import enum
import uuid

from django.db import models


class StockItem(models.Model):
    isbn = models.CharField(max_length=13, unique=True)
    title = models.CharField(max_length=200, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    reserved = models.PositiveIntegerField(default=0)

    @property
    def available(self):
        return self.quantity - self.reserved

    def __str__(self):
        return f"{self.isbn} ({self.available} available)"


class ReservationStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELED = "canceled"


class Reservation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_reference = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20,
        choices=[(item.value, item.name.title()) for item in ReservationStatus],
        default=ReservationStatus.PENDING.value,
    )
    items = models.JSONField(help_text='[{"isbn": "...", "quantity": 2}, ...]')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reservation {self.id} for order {self.order_reference} ({self.status})"
