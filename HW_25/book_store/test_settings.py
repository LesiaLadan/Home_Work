from book_store.settings.development import *  # noqa: F401,F403
from book_store.settings.base import BASE_DIR

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",
    }
}

STRIPE_SECRET_KEY = "sk_test_fake"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}
