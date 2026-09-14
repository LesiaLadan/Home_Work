import pytest

from shop.forms import RatingForm
from user_management.forms import UserRegisterForm, UserLoginForm


def test_rating_form_valid():
    form = RatingForm(
        data={
            "rating": 5,
            "feedback": "Good book",
        }
    )

    assert form.is_valid()


def test_rating_form_without_feedback_is_valid():
    form = RatingForm(
        data={
            "rating": 5,
            "feedback": "",
        }
    )

    assert form.is_valid()


@pytest.mark.django_db
def test_register_form_valid():
    form = UserRegisterForm(
        data={
            "username": "testuser",
            "first_name": "John",
            "last_name": "Smith",
            "email": "test@example.com",
            "phone": "123456789",
            "password1": "TestPassword123!",
            "password2": "TestPassword123!",
        }
    )

    assert form.is_valid()


@pytest.mark.django_db
def test_register_form_passwords_must_match():
    form = UserRegisterForm(
        data={
            "username": "testuser",
            "first_name": "John",
            "last_name": "Smith",
            "email": "test@example.com",
            "phone": "123456789",
            "password1": "TestPassword123!",
            "password2": "DifferentPassword123!",
        }
    )

    assert not form.is_valid()


def test_login_form_has_username_and_password_fields():
    form = UserLoginForm()

    assert "username" in form.fields
    assert "password" in form.fields
