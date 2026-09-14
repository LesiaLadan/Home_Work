from decimal import Decimal

import pytest
from django.urls import reverse
from order.models import Order, OrderDetails, PaymentMethod, PaymentStatus, OrderStatus
from tests.factories import BookFactory, UserFactory
from unittest.mock import patch


@pytest.mark.django_db
def test_main_page_loads(client):
    response = client.get(reverse("shop:main_page"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_registration_page_loads(client):
    response = client.get(reverse("user_management:register"))

    assert response.status_code == 200
    assert "register_form" in response.context


@pytest.mark.django_db
def test_user_can_register(client):
    response = client.post(
        reverse("user_management:register"),
        {
            "username": "newuser",
            "first_name": "John",
            "last_name": "Smith",
            "email": "john@example.com",
            "phone": "123456789",
            "password1": "TestPassword123!",
            "password2": "TestPassword123!",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("user_management:login")


@pytest.mark.django_db
def test_registration_with_wrong_passwords_stays_on_page(client):
    response = client.post(
        reverse("user_management:register"),
        {
            "username": "newuser",
            "first_name": "John",
            "last_name": "Smith",
            "email": "john@example.com",
            "phone": "123456789",
            "password1": "TestPassword123!",
            "password2": "WrongPassword123!",
        },
    )

    assert response.status_code == 200
    assert response.context["register_form"].errors


@pytest.mark.django_db
def test_login_page_loads(client):
    response = client.get(reverse("user_management:login"))

    assert response.status_code == 200
    assert "login_form" in response.context


@pytest.mark.django_db
def test_user_can_login(client):
    user = UserFactory()
    user.set_password("TestPassword123!")
    user.save()

    response = client.post(
        reverse("user_management:login"),
        {
            "username": user.username,
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("shop:main_page")


@pytest.mark.django_db
def test_user_can_logout(client):
    user = UserFactory()
    user.set_password("TestPassword123!")
    user.save()

    client.login(
        username=user.username,
        password="TestPassword123!",
    )

    response = client.post(reverse("user_management:logout"))

    assert response.status_code == 302
    assert response.url == reverse("shop:main_page")


@pytest.mark.django_db
def test_checkout_page_loads(client):
    user = UserFactory()
    client.force_login(user)

    response = client.get(reverse("order:checkout"))

    assert response.status_code == 200
    assert "checkout_data" in response.context
    assert "form" in response.context


@pytest.mark.django_db
def test_order_success_page_loads(client):
    user = UserFactory()
    client.force_login(user)

    response = client.get(reverse("order:order_success"))

    assert response.status_code == 200
    assert "checkout_session_id" in response.context


def test_checkout_requires_login(client):
    response = client.get(reverse("order:checkout"))

    assert response.status_code == 302


@pytest.mark.django_db
def test_place_order_with_empty_cart_redirects_to_cart(client):
    user = UserFactory()
    client.force_login(user)

    response = client.post(
        reverse("order:place_order"),
        {
            "postal_code": "01001",
            "city": "Kyiv",
            "street": "Khreshchatyk",
            "branch": "1",
            "payment_method": PaymentMethod.CASH.value,
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("order:cart")


@pytest.mark.django_db
def test_place_order_creates_order(client):
    user = UserFactory()
    user.set_password("TestPassword123!")
    user.save()

    client.login(
        username=user.username,
        password="TestPassword123!",
    )

    book = BookFactory(
        price=25,
    )

    session = client.session
    session["cart"] = {
        str(book.id): 2,
    }
    session.save()

    data = {
        "postal_code": "01001",
        "city": "Kyiv",
        "street": "Khreshchatyk",
        "branch": "1",
        "payment_method": PaymentMethod.CASH.value,
    }

    with (
        patch("order.views.send_order_confirmation_email.delay") as mock_send_email,
        patch("order.views.reserve_stock", return_value="res-1") as mock_reserve_stock,
        patch("order.views.confirm_reservation") as mock_confirm_reservation,
    ):
        response = client.post(
            reverse("order:place_order"),
            data,
        )

    assert response.status_code == 302

    order = Order.objects.get(owner=user)

    assert order.total_price == Decimal("50")
    assert order.payment_method == PaymentMethod.CASH.value
    assert order.payment_status == PaymentStatus.PENDING.value
    assert order.status == OrderStatus.PENDING.value

    details = OrderDetails.objects.get(order=order)

    assert details.book == book
    assert details.quantity == 2
    assert details.price == Decimal("25")

    mock_reserve_stock.assert_called_once_with(
        order_reference=str(order.pk),
        items=[{"isbn": book.isbn, "quantity": 2}],
    )
    mock_confirm_reservation.assert_called_once_with("res-1")
    mock_send_email.assert_called_once()


@pytest.mark.django_db
def test_place_order_with_card_payment_does_not_confirm_reservation_yet(client):
    """Card orders redirect to Stripe; the reservation is confirmed later by
    the webhook, once payment actually succeeds - not here."""
    user = UserFactory()
    client.force_login(user)
    book = BookFactory(price=25)

    session = client.session
    session["cart"] = {str(book.id): 1}
    session.save()

    data = {
        "postal_code": "01001",
        "city": "Kyiv",
        "street": "Khreshchatyk",
        "branch": "1",
        "payment_method": PaymentMethod.CARD.value,
    }

    with (
        patch("order.views.send_order_confirmation_email.delay"),
        patch("order.views.reserve_stock", return_value="res-2") as mock_reserve_stock,
        patch("order.views.confirm_reservation") as mock_confirm_reservation,
    ):
        response = client.post(reverse("order:place_order"), data)

    order = Order.objects.get(owner=user)
    assert response.status_code == 302
    assert response.url == reverse("order:stripe", args=[order.pk])
    mock_reserve_stock.assert_called_once()
    mock_confirm_reservation.assert_not_called()


@pytest.mark.django_db
def test_place_order_logs_but_succeeds_when_confirm_reservation_fails(client):
    """A cash order is still placed even if stock_api can't be reached to
    confirm the reservation right away - the failure is only logged."""
    from order.stock_client import StockServiceError

    user = UserFactory()
    client.force_login(user)
    book = BookFactory(price=25)

    session = client.session
    session["cart"] = {str(book.id): 1}
    session.save()

    data = {
        "postal_code": "01001",
        "city": "Kyiv",
        "street": "Khreshchatyk",
        "branch": "1",
        "payment_method": PaymentMethod.CASH.value,
    }

    with (
        patch("order.views.send_order_confirmation_email.delay"),
        patch("order.views.reserve_stock", return_value="res-3"),
        patch(
            "order.views.confirm_reservation",
            side_effect=StockServiceError("unavailable"),
        ),
    ):
        response = client.post(reverse("order:place_order"), data)

    assert response.status_code == 302
    assert response.url == reverse("order:order_success")
    assert Order.objects.filter(owner=user).exists()
