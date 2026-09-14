import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import Reservation, ReservationStatus, StockItem

logger = logging.getLogger(__name__)


@shared_task
def cancel_expired_reservations():

    cutoff = timezone.now() - timedelta(hours=settings.RESERVATION_EXPIRY_HOURS)
    expired = Reservation.objects.filter(
        status=ReservationStatus.PENDING.value, created_at__lt=cutoff
    )

    canceled_count = 0
    for reservation in expired:
        with transaction.atomic():
            for item in reservation.items:
                stock = StockItem.objects.get(isbn=item["isbn"])
                stock.reserved -= item["quantity"]
                stock.save(update_fields=["reserved"])

            reservation.status = ReservationStatus.CANCELED.value
            reservation.save(update_fields=["status"])
        canceled_count += 1

    logger.info("cancel_expired_reservations canceled=%s", canceled_count)
    return canceled_count
