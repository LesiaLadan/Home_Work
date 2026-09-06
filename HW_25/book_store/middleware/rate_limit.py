import time

from django.http import HttpResponse


class RateLimitMiddleware:
    """Limits the number of requests from a single IP address"""

    """Limit is set to 10 requests per minute to demonstrate rate limiting funcionality."""
    REQUEST_LIMIT = 100
    TIME_WINDOW = 60

    def __init__(self, get_response):
        self.get_response = get_response
        self.requests = {}

    def __call__(self, request):
        ip = self.get_client_ip(request)
        now = time.time()

        if ip not in self.requests:
            self.requests[ip] = []

        self.requests[ip] = [t for t in self.requests[ip] if now - t < self.TIME_WINDOW]

        if len(self.requests[ip]) >= self.REQUEST_LIMIT:
            return HttpResponse(
                "Too many requests. Please try again later.",
                status=429,
                content_type="text/plain",
            )

        self.requests[ip].append(now)

        return self.get_response(request)

    def get_client_ip(self, request):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")

        if forwarded:
            return forwarded.split(",")[0]

        return request.META.get("REMOTE_ADDR")
