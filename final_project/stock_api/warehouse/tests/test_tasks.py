from datetime import timedelta

import pytest
from django.utils import timezone

from warehouse.models import Reservation, ReservationStatus
from warehouse.tasks import cancel_expired_reservations
from warehouse.tests.factories import ReservationFactory, StockItemFactory

pytestmark = pytest.mark.django_db


def test_cancel_expired_reservations_releases_stock():
    book = StockItemFactory(isbn="9780000000099", quantity=10, reserved=4)
    reservation = ReservationFactory(items=[{"isbn": book.isbn, "quantity": 4}])
    Reservation.objects.filter(pk=reservation.pk).update(
        created_at=timezone.now() - timedelta(hours=48)
    )

    canceled_count = cancel_expired_reservations()

    assert canceled_count == 1
    book.refresh_from_db()
    assert book.reserved == 0
    reservation.refresh_from_db()
    assert reservation.status == ReservationStatus.CANCELED.value


def test_cancel_expired_reservations_ignores_recent_ones():
    book = StockItemFactory(isbn="9780000000098", quantity=10, reserved=2)
    reservation = ReservationFactory(items=[{"isbn": book.isbn, "quantity": 2}])

    canceled_count = cancel_expired_reservations()

    assert canceled_count == 0
    reservation.refresh_from_db()
    assert reservation.status == ReservationStatus.PENDING.value
