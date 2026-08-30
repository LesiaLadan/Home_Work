from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .views import BookViewSet, CartAddView, CartClearView, CartRemoveView, CartView, CategoryViewSet, OrderViewSet

router = DefaultRouter()
router.register("books", BookViewSet, basename="book")
router.register("categories", CategoryViewSet, basename="category")
router.register("orders", OrderViewSet, basename="order")

urlpatterns = [
    path("", include(router.urls)),
    path("cart/", CartView.as_view(), name="cart-list"),
    path("cart/add/", CartAddView.as_view(), name="cart-add"),
    path("cart/remove/", CartRemoveView.as_view(), name="cart-remove"),
    path("cart/clear/", CartClearView.as_view(), name="cart-clear"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]