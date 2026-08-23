from decimal import Decimal

import factory

from order.models import Order, OrderDetails
from shop.models import Author, Book, Category, Publisher, Rating
from user_management.models import DeliveryAddress, LastViewedBooks, User


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


# Generated with AI, reviewed and modified
class DeliveryAddressFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DeliveryAddress

    owner = factory.SubFactory(UserFactory)
    postal_code = "01001"
    city = "Kyiv"
    street = "Khreshchatyk"
    branch = "1"


# Generated with AI, reviewed and modified
class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    owner = factory.SubFactory(UserFactory)
    delivery_address = factory.SubFactory(DeliveryAddressFactory)
    total_price = Decimal("100.00")


# Generated with AI, reviewed and modified
class OrderDetailsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrderDetails

    order = factory.SubFactory(OrderFactory)
    book = factory.SubFactory(BookFactory)
    quantity = 1
    price = Decimal("25.00")


# Generated with AI, reviewed and modified
class LastViewedBooksFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LastViewedBooks

    book = factory.SubFactory(BookFactory)
    owner = factory.SubFactory(UserFactory)
