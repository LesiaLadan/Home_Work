import pytest
from django.conf import settings
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def service_client():
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Service {settings.STOCK_API_TOKEN}")
    return client
