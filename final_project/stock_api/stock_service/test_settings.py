from stock_service.settings.development import *  # noqa: F401,F403
from stock_service.settings.base import BASE_DIR

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",
    }
}

STOCK_API_TOKEN = "test-service-token"
