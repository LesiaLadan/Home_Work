import hashlib
import hmac
import json
import time
from unittest.mock import patch

import pytest
from django.conf import settings
from django.urls import reverse
from order.models import Order, PaymentMethod, PaymentStatus
from tests.factories import OrderFactory


def _signed_request(client, url, payload: dict):
    body = json.dumps(payload).encode()
    timestamp = str(int(time.time()))
    signature = hmac.new(
        settings.STRIPE_WEBHOOK_SECRET.encode(),
        f"{timestamp}.{body.decode()}".encode(),
        hashlib.sha256,
    ).hexdigest()
    header = f"t={timestamp},v1={signature}"
    return client.post(
        url,
        data=body,
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE=header,
    )


def _checkout_completed_event(order_id, event_id="evt_1"):
    return {
        "id": event_id,
        "object": "event",
        "type": "checkout.session.completed",
        "data": {"object": {"metadata": {"order_id": str(order_id)}}},
    }


@pytest.mark.django_db
@patch("order.views.confirm_reservation")
def test_webhook_marks_order_paid_and_confirms_reservation(
    mock_confirm_reservation, client
):
    """Regression test: this used to crash with
    `AttributeError: get` because Stripe's deserialized event/session
    objects don't support dict's .get() - only item access and `in`."""
    order = OrderFactory(
        payment_method=PaymentMethod.CARD.value,
        payment_status=PaymentStatus.PENDING.value,
        reservation_id="res-42",
    )
    url = reverse("order:stripe_webhook")

    response = _signed_request(client, url, _checkout_completed_event(order.pk))

    assert response.status_code == 200
    order.refresh_from_db()
    assert order.payment_status == PaymentStatus.COMPLETED.value
    mock_confirm_reservation.assert_called_once_with("res-42")


@pytest.mark.django_db
@patch("order.views.confirm_reservation")
def test_webhook_duplicate_delivery_is_skipped(mock_confirm_reservation, client):
    order = OrderFactory(
        payment_method=PaymentMethod.CARD.value,
        payment_status=PaymentStatus.COMPLETED.value,
        reservation_id="res-43",
    )
    url = reverse("order:stripe_webhook")

    response = _signed_request(client, url, _checkout_completed_event(order.pk))

    assert response.status_code == 200
    mock_confirm_reservation.assert_not_called()


@pytest.mark.django_db
def test_webhook_unknown_order_returns_404(client):
    url = reverse("order:stripe_webhook")

    response = _signed_request(client, url, _checkout_completed_event(999999))

    assert response.status_code == 404


@pytest.mark.django_db
def test_webhook_missing_order_id_returns_400(client):
    url = reverse("order:stripe_webhook")
    event = {
        "id": "evt_2",
        "object": "event",
        "type": "checkout.session.completed",
        "data": {"object": {"metadata": {}}},
    }

    response = _signed_request(client, url, event)

    assert response.status_code == 400


@pytest.mark.django_db
def test_webhook_invalid_signature_returns_400(client):
    url = reverse("order:stripe_webhook")

    response = client.post(
        url,
        data=json.dumps(_checkout_completed_event(1)).encode(),
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="t=1,v1=not-a-real-signature",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_webhook_ignores_unhandled_event_types(client):
    url = reverse("order:stripe_webhook")
    event = {
        "id": "evt_3",
        "object": "event",
        "type": "payment_intent.created",
        "data": {"object": {}},
    }

    response = _signed_request(client, url, event)

    assert response.status_code == 200
    assert not Order.objects.filter(
        payment_status=PaymentStatus.COMPLETED.value
    ).exists()
