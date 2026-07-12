from django.shortcuts import render, redirect
from .forms import UserRegisterForm, UserLoginForm
from django.contrib.auth import authenticate, login, logout
import structlog

logger = structlog.get_logger(__name__)


def user_registration(request):
    if request.method == "POST":
        register_form = UserRegisterForm(request.POST)
        if register_form.is_valid():
            register_form.save()
            logger.info(
                "New user registered",
                username=user.username,
                email=user.email,
            )
            return redirect("user_management:login")
        else:
            logger.warning("User registration failed", errors=register_form.errors)
    else:
        register_form = UserRegisterForm()

    return render(
        request,
        "user_management/register.html",
        {"register_form": register_form},
    )


def user_login(request):
    if request.method == "POST":
        login_form = UserLoginForm(request=request, data=request.POST)
        if login_form.is_valid():
            username = login_form.cleaned_data.get("username")
            password = login_form.cleaned_data.get("password")
            logger.info("Attempting login for user", username=username)
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                logger.info("User logged in successfully", username=username)
                return redirect("shop:main_page")
        else:
            logger.warning("Login failed", username=request.POST.get("username"))
    else:
        login_form = UserLoginForm(request=request)
    return render(
        request,
        "user_management/login.html",
        {"login_form": login_form},
    )


def user_logout(request):
    username = request.user.username
    logout(request)
    logger.info("User logged out", username=username)
    return redirect("shop:main_page")
