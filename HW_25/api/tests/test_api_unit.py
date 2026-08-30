import pytest
from django.urls import reverse
from rest_framework import status

from shop.models import Book, Category
from tests.factories import (
    AuthorFactory,
    BookFactory,
    CategoryFactory,
    OrderFactory,
    PublisherFactory,
    UserFactory,
)


@pytest.mark.django_db
def test_obtain_token_with_valid_creds(api_client):
    user = UserFactory()
    user.set_password("TestPassword123!")
    user.save()

    response = api_client.post(
        reverse("token_obtain_pair"),
        {"username": user.username, "password": "TestPassword123!"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data


@pytest.mark.django_db
def test_obtain_token_with_invalid_creds(api_client):
    UserFactory()

    response = api_client.post(
        reverse("token_obtain_pair"),
        {"username": "nouser", "password": "wrong"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_refresh_returns_new_token(api_client):
    user = UserFactory()
    user.set_password("TestPassword123!")
    user.save()

    obtain_response = api_client.post(
        reverse("token_obtain_pair"),
        {"username": user.username, "password": "TestPassword123!"},
    )
    refresh_token = obtain_response.data["refresh"]

    response = api_client.post(reverse("token_refresh"), {"refresh": refresh_token})

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data


@pytest.mark.django_db
def test_verify_valid_token(api_client):
    user = UserFactory()
    user.set_password("TestPassword123!")
    user.save()

    obtain_response = api_client.post(
        reverse("token_obtain_pair"),
        {"username": user.username, "password": "TestPassword123!"},
    )
    access_token = obtain_response.data["access"]

    response = api_client.post(reverse("token_verify"), {"token": access_token})

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_verify_invalid_token(api_client):
    response = api_client.post(reverse("token_verify"), {"token": "not-a-real-token"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_book_list_returns_paginated_response(api_client):
    BookFactory.create_batch(25)

    response = api_client.get(reverse("book-list"))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 25
    assert len(response.data["results"]) == 20


@pytest.mark.django_db
def test_book_list_second_page(api_client):
    BookFactory.create_batch(25)

    response = api_client.get(reverse("book-list"), {"page": 2})

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 5


@pytest.mark.django_db
def test_book_list_access_allowed_for_all(api_client):
    BookFactory()

    response = api_client.get(reverse("book-list"))

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_book_filter_by_category(api_client):
    fiction = CategoryFactory(name="Fiction")
    poetry = CategoryFactory(name="Poetry")
    fiction_book = BookFactory()
    fiction_book.category.add(fiction)
    poetry_book = BookFactory()
    poetry_book.category.add(poetry)

    response = api_client.get(reverse("book-list"), {"category": fiction.id})

    ids = [book["id"] for book in response.data["results"]]
    assert fiction_book.id in ids
    assert poetry_book.id not in ids


@pytest.mark.django_db
def test_book_filter_by_price(api_client):
    cheap = BookFactory(price=10)
    expensive = BookFactory(price=500)

    response = api_client.get(reverse("book-list"), {"price_min": 100})

    ids = [book["id"] for book in response.data["results"]]
    assert expensive.id in ids
    assert cheap.id not in ids


@pytest.mark.django_db
def test_book_shows_author_and_category(api_client):
    author = AuthorFactory()
    book = BookFactory()
    book.author.add(author)

    response = api_client.get(reverse("book-detail", args=[book.id]))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["author"][0]["id"] == author.id


@pytest.mark.django_db
def test_book_create_not_allowed_for_not_authenticated(api_client):
    response = api_client.post(reverse("book-list"), {"title": "New Book"})

    assert response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    )


@pytest.mark.django_db
def test_book_create_not_allowed_for_user(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)

    response = api_client.post(reverse("book-list"), {"title": "New Book"})

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_book_create_allowed_for_admin(api_client):
    admin = UserFactory(is_staff=True, is_superuser=True)
    api_client.force_authenticate(user=admin)
    author = AuthorFactory()
    category = CategoryFactory()
    publisher = PublisherFactory()

    response = api_client.post(
        reverse("book-list"),
        {
            "title": "New Book",
            "isbn": "1111111111111",
            "publication_date": "2026-01-01",
            "in_stock": 5,
            "price": "30.00",
            "language": "English",
            "publisher": publisher.id,
            "calculated_avg_rating": 0,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert Book.objects.filter(title="New Book").exists()


@pytest.mark.django_db
def test_category_list(api_client):
    CategoryFactory.create_batch(3)

    response = api_client.get(reverse("category-list"))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 3


@pytest.mark.django_db
def test_create_category_not_allowed_for_not_authenticated(api_client):
    response = api_client.post(reverse("category-list"), {"name": "New"})

    assert response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    )


@pytest.mark.django_db
def test_create_category_not_allowed_for_user(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)

    response = api_client.post(reverse("category-list"), {"name": "New"})

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_create_category_allowed_for_admin(api_client):
    admin = UserFactory(is_staff=True, is_superuser=True)
    api_client.force_authenticate(user=admin)

    response = api_client.post(reverse("category-list"), {"name": "Fantasy"})

    assert response.status_code == status.HTTP_201_CREATED
    assert Category.objects.filter(name="Fantasy").exists()


@pytest.mark.django_db
def test_delete_category_allowed_for_admin(api_client):
    admin = UserFactory(is_staff=True, is_superuser=True)
    api_client.force_authenticate(user=admin)
    category = CategoryFactory()

    response = api_client.delete(reverse("category-detail", args=[category.id]))

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Category.objects.filter(id=category.id).exists()


@pytest.mark.django_db
def test_order_list_requires_authentication(api_client):
    response = api_client.get(reverse("order-list"))

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_order_list_returns_only_owners_orders(api_client):
    user = UserFactory()
    other_user = UserFactory()
    order_owner = OrderFactory(owner=user)
    OrderFactory(owner=other_user)

    api_client.force_authenticate(user=user)
    response = api_client.get(reverse("order-list"))

    ids = [order["id"] for order in response.data["results"]]
    assert ids == [order_owner.id]


@pytest.mark.django_db
def test_order_retrieve_owners_order(api_client):
    user = UserFactory()
    order = OrderFactory(owner=user)

    api_client.force_authenticate(user=user)
    response = api_client.get(reverse("order-detail", args=[order.id]))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == order.id


@pytest.mark.django_db
def test_retrieve_another_users_order_returns_404(api_client):
    user = UserFactory()
    other_user = UserFactory()
    other_order = OrderFactory(owner=other_user)

    api_client.force_authenticate(user=user)
    response = api_client.get(reverse("order-detail", args=[other_order.id]))

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_order_filter_by_status(api_client):
    user = UserFactory()
    pending = OrderFactory(owner=user, status="pending")
    shipped = OrderFactory(owner=user, status="shipped")

    api_client.force_authenticate(user=user)
    response = api_client.get(reverse("order-list"), {"status": "shipped"})

    ids = [order["id"] for order in response.data["results"]]
    assert shipped.id in ids
    assert pending.id not in ids


@pytest.mark.django_db
def test_cart_requires_authentication(api_client):
    response = api_client.get(reverse("cart-list"))

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_cart_starts_empty(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)

    response = api_client.get(reverse("cart-list"))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["items"] == []


@pytest.mark.django_db
def test_add_item_to_cart(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)
    book = BookFactory(price=20, in_stock=5)

    response = api_client.post(reverse("cart-add"), {"book_id": book.id})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["items"][0]["book_id"] == book.id
    assert response.data["items"][0]["quantity"] == 1


@pytest.mark.django_db
def test_delete_item_from_cart(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)
    book = BookFactory(price=20, in_stock=5)
    api_client.post(reverse("cart-add"), {"book_id": book.id})

    response = api_client.post(reverse("cart-remove"), {"book_id": book.id})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["items"] == []


@pytest.mark.django_db
def test_clear_cart(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)
    book = BookFactory(price=20, in_stock=5)
    api_client.post(reverse("cart-add"), {"book_id": book.id})

    response = api_client.post(reverse("cart-clear"))

    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_add_item_to_cart_invalid_payload_returns_400(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)

    response = api_client.post(reverse("cart-add"), {})

    assert response.status_code == status.HTTP_400_BAD_REQUEST