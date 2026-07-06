from django.urls import path
from . import views

app_name = "order"

urlpatterns = [
    path("", views.order_list, name="order_list"),
    path("new/", views.new_order, name="new_order"),
    path("success/", views.order_success, name="order_success"),
    path("<int:order_id>/", views.order_detail, name="order_detail")
]
