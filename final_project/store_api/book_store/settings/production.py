import os

from .base import *  # noqa: F401,F403

# Settings used in production. Unlike development.py, secrets and host
# configuration are required from the environment (via .env_docker /
# real environment variables) instead of falling back to insecure
# defaults - a missing SECRET_KEY or ALLOWED_HOSTS fails loudly at
# startup rather than silently running with a dev secret.

SECRET_KEY = os.environ["SECRET_KEY"]

DEBUG = False

ALLOWED_HOSTS = os.environ["ALLOWED_HOSTS"].split(",")

# Set USE_HTTPS=True once the app is served behind TLS (directly or via
# a reverse proxy setting X-Forwarded-Proto). It is False by default
# because the current docker-compose setup exposes gunicorn on plain
# HTTP, and turning these on without TLS in front would lock users out
# (redirect loops, cookies never sent back).
USE_HTTPS = os.environ.get("USE_HTTPS", "False") == "True"

SECURE_SSL_REDIRECT = USE_HTTPS
SESSION_COOKIE_SECURE = USE_HTTPS
CSRF_COOKIE_SECURE = USE_HTTPS
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30 if USE_HTTPS else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = USE_HTTPS
SECURE_HSTS_PRELOAD = USE_HTTPS
if USE_HTTPS:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Security headers that don't depend on TLS being terminated in front
# of the app.
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# Serve static files straight from gunicorn via WhiteNoise, with
# hashed filenames and gzip/brotli compression, instead of Django's
# plain filesystem storage used in development.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
