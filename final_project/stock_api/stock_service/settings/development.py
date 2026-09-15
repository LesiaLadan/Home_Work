import os

from .base import *  # noqa: F401,F403

# Settings used for local development

SECRET_KEY = os.environ.get(
    "SECRET_KEY", "dev-only-secret-key-do-not-use-in-production"
)

DEBUG = True

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
