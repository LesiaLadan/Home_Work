from django.urls import path
from .views import (
    AddToCartView,
    CartView,
    CheckoutView,
    OrderSuccessView,
    PlaceOrderView,
    RemoveFromCartView,
    create_checkout_session,
    stripe_webhook
)

app_name = "order"

urlpatterns = [
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/add/<int:book_id>/", AddToCartView.as_view(), name="add_to_cart"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("confirm-order/", PlaceOrderView.as_view(), name="place_order"),
    # path("success/<str:checkout_session_id>/", OrderSuccessView.as_view(), name="order_success"),
    path("success/", OrderSuccessView.as_view(), name="order_success"),
    path("stripe/<int:order_id>/", create_checkout_session, name="stripe"),
    path("cart/remove/<int:book_id>/", RemoveFromCartView.as_view(), name="remove_from_cart"),
    path("stripe/webhook/", stripe_webhook, name="stripe_webhook"),
]
