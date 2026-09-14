from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from .views import (
    ReservationCancelView,
    ReservationConfirmView,
    ReservationCreateView,
    ReservationDetailView,
)

urlpatterns = [
    path("reservations/", ReservationCreateView.as_view(), name="reservation-create"),
    path(
        "reservations/<uuid:pk>/",
        ReservationDetailView.as_view(),
        name="reservation-detail",
    ),
    path(
        "reservations/<uuid:pk>/confirm/",
        ReservationConfirmView.as_view(),
        name="reservation-confirm",
    ),
    path(
        "reservations/<uuid:pk>/cancel/",
        ReservationCancelView.as_view(),
        name="reservation-cancel",
    ),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
