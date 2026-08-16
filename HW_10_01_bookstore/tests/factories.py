import factory

from shop.models import Author, Book, Category, Publisher, Rating
from user_management.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Sequence(lambda n: f"user{n}@test.com")


class AuthorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Author

    first_name = "Lesya"
    last_name = "Ukrainka"
    biography = "Test biography"


class PublisherFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Publisher

    name = "Test Publisher"
    city = "Kyiv"
    website = "https://example.com"


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = "Fiction"


class BookFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Book

    title = factory.Sequence(lambda n: f"Book {n}")
    isbn = factory.Sequence(lambda n: f"{n:013d}")
    publication_date = "2025-01-01"
    publisher = factory.SubFactory(PublisherFactory)
    in_stock = 10
    price = 25
    wholesale_price = 20
    language = "English"
    calculated_avg_rating = 4.5


class RatingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Rating

    book = factory.SubFactory(BookFactory)
    user = factory.SubFactory(UserFactory)
    rating = 5
    feedback = "OK"
