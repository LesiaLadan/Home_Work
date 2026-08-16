import pytest
from tests.factories import (
    AuthorFactory,
    BookFactory,
    CategoryFactory,
    PublisherFactory,
    RatingFactory,
    UserFactory,
)


@pytest.mark.django_db
def test_publisher_str():
    publisher = PublisherFactory()

    assert str(publisher) == publisher.name


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


