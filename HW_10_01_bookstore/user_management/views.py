from django.shortcuts import render, redirect
from .forms import UserRegisterForm, UserLoginForm
from django.contrib.auth import authenticate, login, logout


def user_registration(request):
    if request.method == "POST":
        register_form = UserRegisterForm(request.POST)
        if register_form.is_valid():
            register_form.save()
            return redirect("user_management:login")
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
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("shop:main_page")
    else:
        login_form = UserLoginForm(request=request)
    return render(
        request,
        "user_management/login.html",
        {"login_form": login_form},
    )


def user_logout(request):
    logout(request)
    return redirect("shop:main_page")
