import logging

from django.conf import settings
from rest_framework import authentication, exceptions

logger = logging.getLogger(__name__)


class ServiceAccount:
    is_authenticated = True
    is_anonymous = False
    username = "store_api"

    def __str__(self):
        return self.username


class ServiceTokenAuthentication(authentication.BaseAuthentication):

    keyword = "Service"

    def authenticate(self, request):
        header = request.headers.get("Authorization")
        if not header:
            return None

        parts = header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            return None

        token = parts[1]
        if not settings.STOCK_API_TOKEN or token != settings.STOCK_API_TOKEN:
            logger.warning("stock_api_auth_failed: invalid service token")
            raise exceptions.AuthenticationFailed("Invalid service token")

        return (ServiceAccount(), None)

    def authenticate_header(self, request):

        return self.keyword
