import factory

from warehouse.models import Reservation, StockItem


class StockItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StockItem

    isbn = factory.Sequence(lambda n: f"978000000{n:04d}")
    title = factory.Faker("sentence", nb_words=3)
    quantity = 10
    reserved = 0


class ReservationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Reservation

    order_reference = factory.Sequence(lambda n: str(1000 + n))
    items = factory.LazyFunction(lambda: [])
