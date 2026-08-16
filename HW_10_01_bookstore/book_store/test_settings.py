from .settings import *
from book_store.settings import BASE_DIR


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",
    }
}

STRIPE_SECRET_KEY = "sk_test_fake"