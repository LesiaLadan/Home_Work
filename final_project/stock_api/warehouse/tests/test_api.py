import pytest
from django.urls import reverse

from warehouse.models import Reservation, ReservationStatus
from warehouse.tests.factories import ReservationFactory, StockItemFactory

pytestmark = pytest.mark.django_db


def test_reservation_create_requires_service_token(api_client):
    response = api_client.post(reverse("reservation-create"), {}, format="json")
    assert response.status_code == 401


def test_reservation_create_rejects_wrong_token(api_client):
    api_client.credentials(HTTP_AUTHORIZATION="Service wrong-token")
    response = api_client.post(reverse("reservation-create"), {}, format="json")
    assert response.status_code == 401


def test_create_reservation_reserves_stock(service_client):
    book = StockItemFactory(isbn="9780000000001", quantity=10, reserved=0)

    response = service_client.post(
        reverse("reservation-create"),
        {
            "order_reference": "42",
            "items": [{"isbn": book.isbn, "quantity": 3}],
        },
        format="json",
    )

    assert response.status_code == 201
    book.refresh_from_db()
    assert book.reserved == 3
    assert book.available == 7
    reservation = Reservation.objects.get(id=response.data["id"])
    assert reservation.status == ReservationStatus.PENDING.value
    assert reservation.order_reference == "42"


def test_create_reservation_fails_when_stock_insufficient(service_client):
    book = StockItemFactory(isbn="9780000000002", quantity=2, reserved=0)

    response = service_client.post(
        reverse("reservation-create"),
        {
            "order_reference": "43",
            "items": [{"isbn": book.isbn, "quantity": 5}],
        },
        format="json",
    )

    assert response.status_code == 409
    book.refresh_from_db()
    assert book.reserved == 0
    assert not Reservation.objects.filter(order_reference="43").exists()


def test_create_reservation_all_or_nothing_across_items(service_client):
    ok_book = StockItemFactory(isbn="9780000000003", quantity=10, reserved=0)
    short_book = StockItemFactory(isbn="9780000000004", quantity=1, reserved=0)

    response = service_client.post(
        reverse("reservation-create"),
        {
            "order_reference": "44",
            "items": [
                {"isbn": ok_book.isbn, "quantity": 2},
                {"isbn": short_book.isbn, "quantity": 5},
            ],
        },
        format="json",
    )

    assert response.status_code == 409
    ok_book.refresh_from_db()
    assert ok_book.reserved == 0 


def test_confirm_reservation_deducts_stock_permanently(service_client):
    book = StockItemFactory(isbn="9780000000005", quantity=10, reserved=4)
    reservation = ReservationFactory(items=[{"isbn": book.isbn, "quantity": 4}])

    response = service_client.post(
        reverse("reservation-confirm", args=[reservation.id])
    )

    assert response.status_code == 200
    book.refresh_from_db()
    assert book.quantity == 6
    assert book.reserved == 0
    reservation.refresh_from_db()
    assert reservation.status == ReservationStatus.CONFIRMED.value


def test_confirm_is_idempotent(service_client):
    book = StockItemFactory(isbn="9780000000006", quantity=10, reserved=2)
    reservation = ReservationFactory(
        items=[{"isbn": book.isbn, "quantity": 2}],
        status=ReservationStatus.CONFIRMED.value,
    )

    response = service_client.post(
        reverse("reservation-confirm", args=[reservation.id])
    )

    assert response.status_code == 200
    book.refresh_from_db()
    assert book.quantity == 10


def test_cancel_reservation_returns_stock(service_client):
    book = StockItemFactory(isbn="9780000000007", quantity=10, reserved=3)
    reservation = ReservationFactory(items=[{"isbn": book.isbn, "quantity": 3}])

    response = service_client.post(reverse("reservation-cancel", args=[reservation.id]))

    assert response.status_code == 200
    book.refresh_from_db()
    assert book.reserved == 0
    assert book.available == 10
    reservation.refresh_from_db()
    assert reservation.status == ReservationStatus.CANCELED.value


def test_cancel_confirmed_reservation_is_rejected(service_client):
    reservation = ReservationFactory(status=ReservationStatus.CONFIRMED.value)

    response = service_client.post(reverse("reservation-cancel", args=[reservation.id]))

    assert response.status_code == 400


def test_reservation_detail(service_client):
    reservation = ReservationFactory()

    response = service_client.get(reverse("reservation-detail", args=[reservation.id]))

    assert response.status_code == 200
    assert response.data["order_reference"] == reservation.order_reference
