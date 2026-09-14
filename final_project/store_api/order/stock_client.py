import structlog
import requests
from django.conf import settings

logger = structlog.get_logger(__name__)

TIMEOUT_SECONDS = 5


class StockServiceError(Exception):
    """Raised whenever stock_api can't fulfil a request: it's unreachable,
    returns an unexpected error, or - for a new reservation - doesn't have
    enough stock for one of the requested items."""


def _headers():
    return {"Authorization": f"Service {settings.STOCK_API_TOKEN}"}


def reserve_stock(order_reference: str, items: list[dict]) -> str:
    """Ask stock_api to reserve ``items`` for ``order_reference``.

    Returns the new reservation's id. Raises StockServiceError if
    stock_api is unreachable or doesn't have enough stock.
    """
    try:
        response = requests.post(
            f"{settings.STOCK_API_URL}/api/reservations/",
            json={"order_reference": order_reference, "items": items},
            headers=_headers(),
            timeout=TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        logger.error("stock_service_unreachable", action="reserve", error=str(exc))
        raise StockServiceError("Stock service is unavailable.") from exc

    if response.status_code == 409:
        logger.warning(
            "stock_reservation_rejected",
            order_reference=order_reference,
            details=response.json(),
        )
        raise StockServiceError("Not enough stock for one or more items.")

    if response.status_code != 201:
        logger.error(
            "stock_service_error",
            action="reserve",
            status_code=response.status_code,
        )
        raise StockServiceError("Stock service returned an unexpected error.")

    return response.json()["id"]


def confirm_reservation(reservation_id: str) -> None:
    """Tell stock_api the order was paid: the reservation is now final."""
    try:
        response = requests.post(
            f"{settings.STOCK_API_URL}/api/reservations/{reservation_id}/confirm/",
            headers=_headers(),
            timeout=TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        logger.error(
            "stock_service_unreachable",
            action="confirm",
            reservation_id=reservation_id,
            error=str(exc),
        )
        raise StockServiceError("Stock service is unavailable.") from exc

    if response.status_code != 200:
        logger.error(
            "stock_service_error",
            action="confirm",
            reservation_id=reservation_id,
            status_code=response.status_code,
        )
        raise StockServiceError("Stock service returned an unexpected error.")


def cancel_reservation(reservation_id: str) -> None:
    """Tell stock_api the order won't be paid: release the reserved stock."""
    try:
        response = requests.post(
            f"{settings.STOCK_API_URL}/api/reservations/{reservation_id}/cancel/",
            headers=_headers(),
            timeout=TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        logger.error(
            "stock_service_unreachable",
            action="cancel",
            reservation_id=reservation_id,
            error=str(exc),
        )
        raise StockServiceError("Stock service is unavailable.") from exc

    if response.status_code != 200:
        logger.error(
            "stock_service_error",
            action="cancel",
            reservation_id=reservation_id,
            status_code=response.status_code,
        )
        raise StockServiceError("Stock service returned an unexpected error.")
