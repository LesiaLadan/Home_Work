from unittest.mock import Mock, patch

import pytest
import requests

from order.stock_client import (
    StockServiceError,
    cancel_reservation,
    confirm_reservation,
    reserve_stock,
)


def _response(status_code, json_data=None):
    response = Mock()
    response.status_code = status_code
    response.json.return_value = json_data or {}
    response.text = ""
    return response


@patch("order.stock_client.requests.post")
def test_reserve_stock_returns_reservation_id(mock_post):
    mock_post.return_value = _response(201, {"id": "res-1"})

    reservation_id = reserve_stock("42", [{"isbn": "123", "quantity": 1}])

    assert reservation_id == "res-1"
    mock_post.assert_called_once()


@patch("order.stock_client.requests.post")
def test_reserve_stock_raises_on_insufficient_stock(mock_post):
    mock_post.return_value = _response(409, {"error": "insufficient_stock"})

    with pytest.raises(StockServiceError):
        reserve_stock("42", [{"isbn": "123", "quantity": 100}])


@patch("order.stock_client.requests.post")
def test_reserve_stock_raises_when_service_unreachable(mock_post):
    mock_post.side_effect = requests.ConnectionError("boom")

    with pytest.raises(StockServiceError):
        reserve_stock("42", [{"isbn": "123", "quantity": 1}])


@patch("order.stock_client.requests.post")
def test_confirm_reservation_succeeds_on_200(mock_post):
    mock_post.return_value = _response(200)

    confirm_reservation("res-1")  # should not raise

    mock_post.assert_called_once()


@patch("order.stock_client.requests.post")
def test_confirm_reservation_raises_on_error_status(mock_post):
    mock_post.return_value = _response(400)

    with pytest.raises(StockServiceError):
        confirm_reservation("res-1")


@patch("order.stock_client.requests.post")
def test_cancel_reservation_succeeds_on_200(mock_post):
    mock_post.return_value = _response(200)

    cancel_reservation("res-1")  # should not raise


@patch("order.stock_client.requests.post")
def test_cancel_reservation_raises_when_service_unreachable(mock_post):
    mock_post.side_effect = requests.Timeout("boom")

    with pytest.raises(StockServiceError):
        cancel_reservation("res-1")
