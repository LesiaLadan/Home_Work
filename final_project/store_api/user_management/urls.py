from django.urls import path

from .views import user_logout, user_registration, user_login

app_name = "user_management"
urlpatterns = [
    path("register/", user_registration, name="register"),
    path("login/", user_login, name="login"),
    path("logout/", user_logout, name="logout"),
]
