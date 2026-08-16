from decimal import Decimal

import pytest
from django.urls import reverse
from order.models import Order, OrderDetails, PaymentMethod, PaymentStatus, OrderStatus
from tests.factories import BookFactory, UserFactory
from unittest.mock import patch, Mock


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
        in_stock=10,
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

    with patch("order.views.send_mail") as mock_send_mail:
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

    book.refresh_from_db()
    assert book.in_stock == 8

    mock_send_mail.assert_called_once()
