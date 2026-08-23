from django.db.models.aggregates import Avg
import pytest
from unittest.mock import patch
from django.urls import reverse
from order.models import Order, PaymentMethod, PaymentStatus
from shop.models import Rating
from tests.factories import AuthorFactory, BookFactory, RatingFactory, UserFactory
from user_management.models import User


@pytest.mark.django_db
def test_user_registration_happy_flow(client):
    response = client.post(
        reverse("user_management:register"),
        {
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "phone": "+380671234567",
            "password1": "StrongPassword123!",
            "password2": "StrongPassword123!",
        },
    )

    assert response.status_code == 302

    assert User.objects.filter(
        username="testuser",
        email="test@example.com",
    ).exists()


@pytest.mark.django_db
def test_user_login_happy_flow(client):
    user = UserFactory()
    user.set_password("StrongPassword123!")
    user.save()

    response = client.post(
        reverse("user_management:login"),
        {
            "username": user.username,
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 302
    assert response.wsgi_request.user.is_authenticated


@pytest.mark.django_db
def test_user_login_invalid_password(client):
    user = UserFactory()
    user.set_password("StrongPassword123!")
    user.save()

    response = client.post(
        reverse("user_management:login"),
        {
            "username": user.username,
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 200
    assert not response.wsgi_request.user.is_authenticated


@pytest.mark.django_db
def test_user_logout_happy_flow(client):
    user = UserFactory()
    user.set_password("StrongPassword123!")
    user.save()

    client.login(username=user.username, password="StrongPassword123!")

    response = client.get(reverse("user_management:logout"))

    assert response.status_code == 302
    assert not response.wsgi_request.user.is_authenticated


@pytest.mark.django_db
def test_books_list(client):
    book1 = BookFactory(title="Book_1")
    book2 = BookFactory(title="Book_2")

    response = client.get(reverse("shop:books_list"))

    assert response.status_code == 200
    assert book1.title in response.content.decode()
    assert book2.title in response.content.decode()


@pytest.mark.django_db
def test_book_details(client):
    book = BookFactory(title="Book_1")

    response = client.get(reverse("shop:book_detail", args=[book.id]))

    assert response.status_code == 200
    assert book.title in response.content.decode()


@pytest.mark.django_db
def test_search_books(client):
    BookFactory(title="Easy Django")
    BookFactory(title="Algorithms")

    response = client.get(
        reverse("shop:books_list"),
        {"q": "Django"},
    )

    assert response.status_code == 200
    assert "Easy Django" in response.content.decode()
    assert "Algorithms" not in response.content.decode()


@pytest.mark.django_db
def test_books_list_pagination_5(client):
    for i in range(6):
        BookFactory(title=f"Book_{i}")

    response = client.get(
        reverse("shop:books_list"),
    )

    assert response.status_code == 200
    assert len(response.context["books"]) == 5
    assert response.context["is_paginated"] is True
    assert response.context["page_obj"].number == 1
    assert response.context["page_obj"].paginator.num_pages == 2

    response = client.get(
        reverse("shop:books_list"),
        {"page": 2},
    )

    assert response.status_code == 200
    assert len(response.context["books"]) == 1
    assert response.context["page_obj"].number == 2


@pytest.mark.django_db
def test_authors_list(client):
    author1 = AuthorFactory(first_name="Lesya", last_name="Ukrainka")
    author2 = AuthorFactory(first_name="Pavlo", last_name="Tychyna")

    response = client.get(reverse("shop:authors_list"))

    assert response.status_code == 200
    assert author1.first_name in response.content.decode()
    assert author2.first_name in response.content.decode()


@pytest.mark.django_db
def test_search_authors(client):
    author = AuthorFactory(
        first_name="Lesya",
        last_name="Ukrainka",
    )
    other_author = AuthorFactory(
        first_name="Pavlo",
        last_name="Tychyna",
    )

    response = client.get(
        reverse("shop:authors_list"),
        {"q": "Lesya"},
    )

    assert response.status_code == 200

    content = response.content.decode()

    assert author.first_name in content
    assert other_author.first_name not in content


@pytest.mark.django_db
def test_author_details(client):
    author = AuthorFactory(
        first_name="Lesya",
        last_name="Ukrainka",
        biography="Test biography",
    )

    response = client.get(reverse("shop:author_detail", args=[author.id]))

    assert response.status_code == 200
    assert author.first_name in response.content.decode()
    assert author.last_name in response.content.decode()
    assert author.biography in response.content.decode()


@pytest.mark.django_db
def test_authors_list_pagination(client):
    for i in range(4):
        AuthorFactory(
            first_name=f"Author{i}",
            last_name="Test",
        )

    response = client.get(reverse("shop:authors_list"))

    assert response.status_code == 200
    assert len(response.context["authors"]) == 3
    assert response.context["is_paginated"] is True
    assert response.context["page_obj"].number == 1
    assert response.context["page_obj"].paginator.num_pages == 2

    response = client.get(
        reverse("shop:authors_list"),
        {"page": 2},
    )

    assert response.status_code == 200
    assert len(response.context["authors"]) == 1
    assert response.context["page_obj"].number == 2


@pytest.mark.django_db
def test_add_book_to_cart(client):
    user = UserFactory()
    user.set_password("StrongPassword123!")
    user.save()

    client.login(username=user.username, password="StrongPassword123!")

    book = BookFactory(title="Book_1")

    response = client.post(reverse("order:add_to_cart", args=[book.id]))

    assert response.status_code == 302

    response = client.get(reverse("order:cart"))

    assert response.status_code == 200
    assert book.title in response.content.decode()


@pytest.mark.django_db
def test_delete_book_from_cart(client):
    user = UserFactory()
    user.set_password("StrongPassword123!")
    user.save()

    client.login(
        username=user.username,
        password="StrongPassword123!",
    )

    book = BookFactory(title="Book_1")

    client.post(reverse("order:add_to_cart", args=[book.id]))

    response = client.post(reverse("order:remove_from_cart", args=[book.id]))

    assert response.status_code == 302

    response = client.get(reverse("order:cart"))

    assert response.status_code == 200
    assert book.title not in response.content.decode()


@pytest.mark.django_db
@patch("order.views.send_mail")
def test_create_order(mock_send_mail, client):
    user = UserFactory()
    user.set_password("StrongPassword123!")
    user.save()

    client.login(
        username=user.username,
        password="StrongPassword123!",
    )

    book = BookFactory(
        title="Book_1",
        in_stock=10,
        price=25,
    )

    client.post(reverse("order:add_to_cart", args=[book.id]))

    response = client.post(
        reverse("order:place_order"),
        {
            "postal_code": "01001",
            "city": "Kyiv",
            "street": "Khoryva",
            "branch": "10",
            "payment_method": PaymentMethod.CASH.value,
        },
    )

    assert response.status_code == 302

    order = Order.objects.get(owner=user)

    assert order.total_price == 25
    assert order.payment_method == PaymentMethod.CASH.value
    assert order.payment_status == PaymentStatus.PENDING.value

    assert order.order_details.filter(
        book=book,
        quantity=1,
        price=25,
    ).exists()

    book.refresh_from_db()
    assert book.in_stock == 9

    mock_send_mail.assert_called_once()

    response = client.get(reverse("order:cart"))

    assert response.status_code == 200
    assert "Your cart is empty" in response.content.decode()


@pytest.mark.django_db
def test_create_order_empty_cart(client):
    user = UserFactory()
    user.set_password("StrongPassword123!")
    user.save()

    client.login(
        username=user.username,
        password="StrongPassword123!",
    )

    response = client.post(
        reverse("order:place_order"),
        {
            "postal_code": "01001",
            "city": "Kyiv",
            "street": "Khoryva",
            "branch": "10",
            "payment_method": PaymentMethod.CASH.value,
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("order:cart")
    assert not Order.objects.filter(owner=user).exists()


@pytest.mark.django_db
def test_create_order_not_enough_in_stock(client):
    user = UserFactory()
    user.set_password("StrongPassword123!")
    user.save()

    client.login(
        username=user.username,
        password="StrongPassword123!",
    )

    book = BookFactory(
        title="Book_1",
        in_stock=0,
    )

    client.post(reverse("order:add_to_cart", args=[book.id]))

    response = client.post(
        reverse("order:place_order"),
        {
            "postal_code": "01001",
            "city": "Kyiv",
            "street": "Khoryva",
            "branch": "10",
            "payment_method": PaymentMethod.CASH.value,
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("order:cart")

    assert not Order.objects.filter(owner=user).exists()

    book.refresh_from_db()
    assert book.in_stock == 0


@pytest.mark.django_db
def test_add_feedback_happy_flow(client):
    user = UserFactory()
    user.set_password("StrongPassword123!")
    user.save()

    client.login(
        username=user.username,
        password="StrongPassword123!",
    )

    book = BookFactory(
        title="Book_1",
        calculated_avg_rating=0,
    )

    response = client.post(
        reverse("shop:add_feedback", args=[book.id]),
        {
            "rating": 5,
            "feedback": "Excellent book!",
        },
    )

    assert response.status_code == 302

    rating = Rating.objects.get(
        book=book,
        user=user,
    )

    assert rating.rating == 5
    assert rating.feedback == "Excellent book!"

    book.refresh_from_db()
    assert book.calculated_avg_rating == 5


@pytest.mark.django_db
def test_edit_feedback_happy_flow(client):
    user = UserFactory()
    user.set_password("StrongPassword123!")
    user.save()

    client.login(
        username=user.username,
        password="StrongPassword123!",
    )

    book = BookFactory(
        title="Book_1",
        calculated_avg_rating=3,
    )

    rating = RatingFactory(
        book=book,
        user=user,
        rating=3,
        feedback="Good book",
    )

    response = client.post(
        reverse("shop:update_feedback", args=[rating.id]),
        {
            "rating": 5,
            "feedback": "Excellent book!",
        },
    )

    assert response.status_code == 302

    rating.refresh_from_db()

    assert rating.rating == 5
    assert rating.feedback == "Excellent book!"

    book.refresh_from_db()
    assert book.calculated_avg_rating == 5


@pytest.mark.django_db
def test_delete_feedback_happy_flow(client):
    user = UserFactory()
    user.set_password("StrongPassword123!")
    user.save()

    client.login(
        username=user.username,
        password="StrongPassword123!",
    )

    book = BookFactory(
        title="Book_1",
        calculated_avg_rating=5,
    )

    rating = RatingFactory(
        book=book,
        user=user,
        rating=5,
        feedback="Excellent book",
    )

    response = client.post(reverse("shop:delete_feedback", args=[rating.id]))

    assert response.status_code == 302
    assert not Rating.objects.filter(pk=rating.id).exists()


@pytest.mark.django_db
def test_recalculate_book_rating_after_feedback_delete():
    user1 = UserFactory()
    user2 = UserFactory()

    book = BookFactory()

    RatingFactory(
        book=book,
        user=user1,
        rating=5,
    )

    RatingFactory(
        book=book,
        user=user2,
        rating=3,
    )

    avg = Rating.objects.filter(book=book).aggregate(Avg("rating"))["rating__avg"]

    book.calculated_avg_rating = avg or 0
    book.save()

    assert book.calculated_avg_rating == 4

    Rating.objects.filter(
        book=book,
        user=user1,
    ).delete()

    avg = Rating.objects.filter(book=book).aggregate(Avg("rating"))["rating__avg"]

    book.calculated_avg_rating = avg or 0
    book.save()

    book.refresh_from_db()

    assert book.calculated_avg_rating == 3
