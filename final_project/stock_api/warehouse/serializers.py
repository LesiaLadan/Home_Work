from rest_framework import serializers

from .models import Reservation


class ReservationItemSerializer(serializers.Serializer):
    isbn = serializers.CharField(max_length=13)
    quantity = serializers.IntegerField(min_value=1)


class ReservationCreateSerializer(serializers.Serializer):
    order_reference = serializers.CharField(max_length=100)
    items = ReservationItemSerializer(many=True, allow_empty=False)


class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ("id", "order_reference", "status", "items", "created_at")
        read_only_fields = fields
