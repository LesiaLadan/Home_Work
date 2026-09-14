from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from order.models import Order, OrderStatus, PaymentMethod, PaymentStatus
from order.stock_client import StockServiceError
from order.tasks import cancel_stale_orders
from tests.factories import OrderFactory


@pytest.mark.django_db
@patch("order.tasks.cancel_reservation")
def test_cancel_stale_orders_cancels_old_unpaid_card_orders(mock_cancel_reservation):
    order = OrderFactory(
        payment_method=PaymentMethod.CARD.value,
        payment_status=PaymentStatus.PENDING.value,
        status=OrderStatus.PENDING.value,
        reservation_id="res-1",
    )
    Order.objects.filter(pk=order.pk).update(
        order_date=timezone.now() - timedelta(hours=48)
    )

    canceled_count = cancel_stale_orders()

    assert canceled_count == 1
    mock_cancel_reservation.assert_called_once_with("res-1")
    order.refresh_from_db()
    assert order.status == OrderStatus.CANCELED.value


@pytest.mark.django_db
@patch("order.tasks.cancel_reservation")
def test_cancel_stale_orders_ignores_recent_orders(mock_cancel_reservation):
    OrderFactory(
        payment_method=PaymentMethod.CARD.value,
        payment_status=PaymentStatus.PENDING.value,
        reservation_id="res-2",
    )

    canceled_count = cancel_stale_orders()

    assert canceled_count == 0
    mock_cancel_reservation.assert_not_called()


@pytest.mark.django_db
@patch("order.tasks.cancel_reservation")
def test_cancel_stale_orders_keeps_order_when_stock_service_unreachable(
    mock_cancel_reservation,
):
    mock_cancel_reservation.side_effect = StockServiceError("unavailable")
    order = OrderFactory(
        payment_method=PaymentMethod.CARD.value,
        payment_status=PaymentStatus.PENDING.value,
        status=OrderStatus.PENDING.value,
        reservation_id="res-3",
    )
    Order.objects.filter(pk=order.pk).update(
        order_date=timezone.now() - timedelta(hours=48)
    )

    canceled_count = cancel_stale_orders()

    assert canceled_count == 0
    order.refresh_from_db()
    assert order.status == OrderStatus.PENDING.value
