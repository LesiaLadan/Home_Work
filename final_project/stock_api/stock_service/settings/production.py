import os

from .base import *  # noqa: F401,F403

# Settings used in production. Secrets and host configuration are
# required from the environment instead of falling back to insecure
# defaults - a missing SECRET_KEY or ALLOWED_HOSTS fails loudly at
# startup rather than silently running with a dev secret.

SECRET_KEY = os.environ["SECRET_KEY"]

DEBUG = False

ALLOWED_HOSTS = os.environ["ALLOWED_HOSTS"].split(",")

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
