import pytest

from warehouse.models import ReservationStatus
from warehouse.tests.factories import ReservationFactory, StockItemFactory

pytestmark = pytest.mark.django_db


def test_stock_item_available_is_quantity_minus_reserved():
    stock = StockItemFactory(quantity=10, reserved=3)
    assert stock.available == 7


def test_reservation_defaults_to_pending():
    reservation = ReservationFactory()
    assert reservation.status == ReservationStatus.PENDING.value


def test_stock_item_str_shows_available():
    stock = StockItemFactory(isbn="9780000000001", quantity=5, reserved=2)
    assert "9780000000001" in str(stock)
    assert "3" in str(stock)
