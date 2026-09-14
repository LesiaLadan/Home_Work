"""
URL configuration for stock_service project.
"""

from django.contrib import admin
from django.urls import include, path

from .views import health_check

urlpatterns = [
    path("health/", health_check, name="health_check"),
    path("admin/", admin.site.urls),
    path("api/", include("warehouse.urls")),
]
