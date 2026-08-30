from rest_framework import serializers

from order.models import Order, OrderDetails
from shop.models import Author, Book, Category, Publisher


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "first_name", "last_name", "biography"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = ["id", "name", "city", "website"]


class BookSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(many=True, read_only=True)
    category = CategorySerializer(many=True, read_only=True)

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "isbn",
            "publication_date",
            "added_date",
            "in_stock",
            "price",
            "wholesale_price",
            "language",
            "description",
            "calculated_avg_rating",
            "author",
            "category",
            "publisher",
        ]
        read_only_fields = ["added_date"]


class OrderDetailsSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)

    class Meta:
        model = OrderDetails
        fields = ["id", "book", "quantity", "price"]


class OrderSerializer(serializers.ModelSerializer):
    order_details = OrderDetailsSerializer(many=True, read_only=True)
    owner = serializers.ReadOnlyField(source="owner.username")

    class Meta:
        model = Order
        fields = [
            "id",
            "owner",
            "delivery_address",
            "order_date",
            "status",
            "total_price",
            "payment_method",
            "payment_status",
            "ttn",
            "order_details",
        ]
        read_only_fields = fields


class CartItemSerializer(serializers.Serializer):
    book_id = serializers.IntegerField()
    title = serializers.CharField()
    price = serializers.DecimalField(max_digits=8, decimal_places=2)
    quantity = serializers.IntegerField()
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)


class CartSerializer(serializers.Serializer):
    items = CartItemSerializer(many=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2)


class CartAddSerializer(serializers.Serializer):
    book_id = serializers.IntegerField()
