import os

from .base import *  # noqa: F401,F403

# Settings used for local development.

SECRET_KEY = os.environ.get(
    "SECRET_KEY", "qu-lr0jn+g0+i23%=9o5%v)78w)!pnrjb1g)ur=l_5h^4pg#-$"
)

DEBUG = True

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Not served over HTTPS locally, so the browser must be allowed to send
# these cookies over plain HTTP.
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
