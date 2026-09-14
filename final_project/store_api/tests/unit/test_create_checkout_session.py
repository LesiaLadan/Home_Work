from unittest.mock import Mock, patch

import pytest
from django.test import Client
from django.urls import reverse
from order.models import PaymentMethod
from tests.factories import OrderFactory, UserFactory


@pytest.mark.django_db
@patch("order.views.stripe.checkout.Session.create")
def test_checkout_session_urls_match_the_host_the_user_is_on(mock_session_create):
    """Regression test: success_url/cancel_url used to be hardcoded to
    localhost:8000. A user browsing via a different host (127.0.0.1,
    a real domain, ...) would get redirected back to a host that
    doesn't share their session cookie, and would appear logged out."""
    mock_session_create.return_value = Mock(url="https://checkout.stripe.com/fake")

    user = UserFactory()
    user.set_password("StrongPassword123!")
    user.save()
    order = OrderFactory(owner=user, payment_method=PaymentMethod.CARD.value)

    client = Client(SERVER_NAME="127.0.0.1")
    assert client.login(username=user.username, password="StrongPassword123!")

    client.get(reverse("order:stripe", args=[order.pk]))

    _, kwargs = mock_session_create.call_args
    assert kwargs["success_url"].startswith("http://127.0.0.1/orders/success/")
    assert kwargs["cancel_url"].startswith("http://127.0.0.1/orders/checkout/")
    assert "localhost" not in kwargs["success_url"]
    assert "localhost" not in kwargs["cancel_url"]
