import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "book_store.settings.development")

app = Celery("book_store")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
