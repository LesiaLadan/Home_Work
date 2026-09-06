from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from order.models import Order, OrderStatus, PaymentMethod, PaymentStatus
from user_management.models import LastViewedBooks, User
from tests.factories import (
    AuthorFactory,
    BookFactory,
    CategoryFactory,
    DeliveryAddressFactory,
    LastViewedBooksFactory,
    OrderDetailsFactory,
    OrderFactory,
    PublisherFactory,
    RatingFactory,
    UserFactory,
)


@pytest.mark.django_db
def test_publisher_str():
    publisher = PublisherFactory()

    assert str(publisher) == publisher.name


# Generated with AI, reviewed and modified
@pytest.mark.django_db
def test_publisher_repr():
    publisher = PublisherFactory()

    assert repr(publisher) == (
        f"Publisher: {publisher.name}, City: {publisher.city}, "
        f"Website: {publisher.website}"
    )


@pytest.mark.django_db
def test_author_str():
    author = AuthorFactory()

    assert str(author) == f"{author.first_name} {author.last_name}"


@pytest.mark.django_db
def test_category_str():
    category = CategoryFactory()

    assert str(category) == category.name


@pytest.mark.django_db
def test_book_str():
    book = BookFactory()
    author = AuthorFactory()
    book.author.add(author)

    assert str(book) == f"{book.title} by {author}"


@pytest.mark.django_db
def test_rating_str():
    rating = RatingFactory()

    assert str(rating) == f"{rating.book.title} - {rating.user.username}"


@pytest.mark.django_db
def test_book_has_author():
    book = BookFactory()
    author = AuthorFactory()

    book.author.add(author)

    assert author in book.author.all()


@pytest.mark.django_db
def test_book_has_category():
    book = BookFactory()
    category = CategoryFactory()

    book.category.add(category)

    assert category in book.category.all()


@pytest.mark.django_db
def test_rating_belongs_to_book():
    rating = RatingFactory()

    assert rating.book is not None


@pytest.mark.django_db
def test_rating_belongs_to_user():
    rating = RatingFactory()

    assert rating.user is not None


# ---------------------------------------------------------------------------
# shop.models.Book
# ---------------------------------------------------------------------------


# Generated with AI, reviewed and modified
@pytest.mark.django_db
def test_book_repr():
    book = BookFactory()
    author = AuthorFactory()
    book.author.add(author)

    assert repr(book) == f"{book.title} by {author}"


# Generated with AI, reviewed and modified
@pytest.mark.django_db
def test_book_isbn_must_be_unique():
    BookFactory(isbn="1111111111111")

    with transaction.atomic():
        with pytest.raises(IntegrityError):
            BookFactory(isbn="1111111111111")


# Generated with AI, reviewed and modified
@pytest.mark.django_db
def test_book_invalid_without_title():
    book = BookFactory.build(title="")

    with pytest.raises(ValidationError) as exc_info:
        book.full_clean(exclude=["publisher"])

    assert "title" in exc_info.value.message_dict


# Generated with AI, reviewed and modified
@pytest.mark.django_db
def test_book_invalid_negative_in_stock():
    book = BookFactory.build(in_stock=-1)

    with pytest.raises(ValidationError) as exc_info:
        book.full_clean(exclude=["publisher"])

    assert "in_stock" in exc_info.value.message_dict


# Generated with AI, reviewed and modified
@pytest.mark.django_db
def test_book_wholesale_price_is_optional():
    book = BookFactory.build(wholesale_price=None)

    # publisher is excluded: an unsaved (build-strategy) related object has
    # no pk yet, which full_clean would otherwise reject independently of
    # the wholesale_price check this test targets.
    book.full_clean(exclude=["publisher"])

    assert book.wholesale_price is None


# Generated with AI, reviewed and modified
@pytest.mark.django_db
def test_book_supports_multiple_authors():
    book = BookFactory()
    author1 = AuthorFactory(first_name="Lesya", last_name="Ukrainka")
    author2 = AuthorFactory(first_name="Ivan", last_name="Franko")

    book.author.add(author1, author2)

    assert book.author.count() == 2
    assert {author1, author2} == set(book.author.all())


# Generated with AI, reviewed and modified
@pytest.mark.django_db
def test_book_supports_multiple_categories():
    book = BookFactory()
    category1 = CategoryFactory(name="Fiction")
    category2 = CategoryFactory(name="Poetry")

    book.category.add(category1, category2)

    assert book.category.count() == 2
    assert {category1, category2} == set(book.category.all())


# ---------------------------------------------------------------------------
# order.models.Order / OrderDetails
# ---------------------------------------------------------------------------


# Generated with AI, reviewed and modified
@pytest.mark.django_db
def test_order_str():
    order = OrderFactory()

    assert str(order) == f"Order {order.pk}"


# Generated with AI, reviewed and modified
@pytest.mark.django_db
def test_order_default_values():
    order = OrderFactory()

    assert order.status == OrderStatus.PENDING.value
    assert order.payment_status == PaymentStatus.PENDING.value
    assert order.payment_method == PaymentMethod.CASH.value
    assert order.ttn in (None, "")


# Generated with AI, reviewed and modified
@pytest.mark.django_db
def test_order_ttn_is_optional():
    order = OrderFactory.build(ttn=None)

    order.owner = UserFactory()
    order.delivery_address = DeliveryAddressFactory()

    order.full_clean(exclude=["owner", "delivery_address"])


# Generated with AI, reviewed and modified
@pytest.mark.django_db
def test_order_owner_relationship():
    user = UserFactory()
    order = OrderFactory(owner=user)

    assert order.owner == user
    assert order in user.orders.all()


# Generated with AI, reviewed and modified
@pytest.mark.django_db
def test_order_delivery_address_relationship():
    address = DeliveryAddressFactory()
    order = OrderFactory(delivery_address=address)

    assert order.delivery_address == address


# Generated with AI, reviewed and modified
@pytest.mark.django_db
@pytest.mark.parametrize("status", list(OrderStatus))
def test_order_status_choices_accept_every_enum_value(status):
    order = OrderFactory(status=status.value)

    order.full_clean()
    assert order.status == status.value


# Generated with AI, reviewed and modified
@pytest.mark.django_db
@pytest.mark.parametrize("payment_method", list(PaymentMethod))
def test_order_payment_method_choices_accept_every_enum_value(payment_method):
    order = OrderFactory(payment_method=payment_method.value)

    order.full_clean()
    assert order.payment_method == payment_method.value


# Generated with AI, reviewed and modified
@pytest.mark.django_db
@pytest.mark.parametrize("payment_status", list(PaymentStatus))
def test_order_payment_status_choices_accept_every_enum_value(payment_status):
    order = OrderFactory(payment_status=payment_status.value)

    order.full_clean()
    assert order.payment_status == payment_status.value


# Generated with AI, reviewed and modified
def test_order_status_field_choices_match_enum():
    expected = [(item.value, item.name.title()) for item in OrderStatus]

    assert Order._meta.get_field("status").choices == expected


# Generated with AI, reviewed and modified
def test_order_payment_method_field_choices_match_enum():
    expected = [(item.value, item.name.title()) for item in PaymentMethod]

    assert Order._meta.get_field("payment_method").choices == expected


# Generated with AI, reviewed and modified
def test_order_payment_status_field_choices_match_enum():
    expected = [(item.value, item.name.title()) for item in PaymentStatus]

    assert Order._meta.get_field("payment_status").choices == expected


# Generated with AI, reviewed and modified
@pytest.mark.django_db
def test_order_details_str():
    details = OrderDetailsFactory(quantity=3)

    assert str(details) == f"{details.book.title}, {details.order.id}, 3"


# Generated with AI, reviewed and modified
@pytest.mark.django_db
def test_order_details_relationship_via_related_name():
    order = OrderFactory()
    details = OrderDetailsFactory(order=order)

    assert details in order.order_details.all()


# Generated with AI, reviewed and modified
@pytest.mark.django_db
def test_order_details_invalid_negative_quantity():
    details = OrderDetailsFactory.build(quantity=-1)

    with pytest.raises(ValidationError):
        details.full_clean(exclude=["order", "book"])


# ---------------------------------------------------------------------------
# user_management.models.User / DeliveryAddress / LastViewedBooks
# ---------------------------------------------------------------------------


# Generated with AI, reviewed and modified
@pytest.mark.django_db
def test_user_str_uses_full_name_when_available():
    user = UserFactory(first_name="Lesya", last_name="Ukrainka")

    assert str(user) == "Lesya Ukrainka"


# Generated with AI, reviewed and modified
@pytest.mark.django_db
def test_user_str_falls_back_to_username_without_full_name():
    user = UserFactory(first_name="", last_name="")

    assert str(user) == user.username


# Generated with AI, reviewed and modified
@pytest.mark.django_db
def test_user_phone_defaults_to_blank():
    user = UserFactory()

    assert user.phone == ""


# Generated with AI, reviewed and modified
@pytest.mark.django_db
def test_user_birth_date_is_optional():
    user = UserFactory.build(username="nobirthdate", birth_date=None)

    # password is excluded: the factory doesn't set one, and that's
    # unrelated to what this test is checking (birth_date nullability).
    user.full_clean(exclude=["password"])
    assert user.birth_date is None


# Generated with AI, reviewed and modified
def test_user_username_must_be_unique_field():
    assert User._meta.get_field("username").unique is True


# Generated with AI, reviewed and modified
@pytest.mark.django_db
def test_delivery_address_str():
    address = DeliveryAddressFactory(
        city="Kyiv", street="Khreshchatyk", postal_code="01001"
    )

    assert str(address) == (f"{address.owner.username} - Kyiv, Khreshchatyk, 01001")


# Generated with AI, reviewed and modified
@pytest.mark.django_db
def test_delivery_address_branch_is_optional():
    address = DeliveryAddressFactory.build(branch=None)
    address.owner = UserFactory()

    address.full_clean(exclude=["owner"])
    assert address.branch is None


# Generated with AI, reviewed and modified
@pytest.mark.django_db
def test_delivery_address_owner_relationship():
    user = UserFactory()
    address = DeliveryAddressFactory(owner=user)

    assert address.owner == user


# Generated with AI, reviewed and modified
@pytest.mark.django_db
def test_last_viewed_books_str():
    entry = LastViewedBooksFactory()

    assert str(entry) == f"{entry.owner.username} - {entry.book.title}"


# Generated with AI, reviewed and modified
@pytest.mark.django_db
def test_last_viewed_books_unique_together_book_and_owner():
    user = UserFactory()
    book = BookFactory()

    LastViewedBooksFactory(book=book, owner=user)

    with transaction.atomic():
        with pytest.raises(IntegrityError):
            LastViewedBooksFactory(book=book, owner=user)


# Generated with AI, reviewed and modified
@pytest.mark.django_db
def test_last_viewed_books_same_book_allowed_for_different_owners():
    book = BookFactory()

    first = LastViewedBooksFactory(book=book)
    second = LastViewedBooksFactory(book=book)

    assert first.owner != second.owner
    assert LastViewedBooks.objects.filter(book=book).count() == 2


# Generated with AI, reviewed and modified
@pytest.mark.django_db
def test_last_viewed_books_default_ordering_is_most_recent_first():
    user = UserFactory()

    older = LastViewedBooksFactory(owner=user)
    newer = LastViewedBooksFactory(owner=user)

    LastViewedBooks.objects.filter(pk=older.pk).update(
        viewed_at=timezone.now() - timedelta(days=1)
    )

    ordered = list(LastViewedBooks.objects.filter(owner=user))

    assert ordered == [newer, older]
