import logging

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Reservation, ReservationStatus, StockItem
from .serializers import ReservationCreateSerializer, ReservationSerializer

logger = logging.getLogger(__name__)


class ReservationCreateView(APIView):
    """reserve stock for a new store_api order"""

    def post(self, request):
        serializer = ReservationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order_reference = serializer.validated_data["order_reference"]
        items = serializer.validated_data["items"]

        with transaction.atomic():
            stock_by_isbn = {
                stock.isbn: stock
                for stock in StockItem.objects.filter(
                    isbn__in=[item["isbn"] for item in items]
                )
            }

            shortages = []
            for item in items:
                stock = stock_by_isbn.get(item["isbn"])
                if stock is None or stock.available < item["quantity"]:
                    shortages.append(
                        {
                            "isbn": item["isbn"],
                            "requested": item["quantity"],
                            "available": stock.available if stock else 0,
                        }
                    )

            if shortages:
                logger.info(
                    "stock_reservation_rejected order=%s shortages=%s",
                    order_reference,
                    shortages,
                )
                return Response(
                    {"error": "insufficient_stock", "items": shortages},
                    status=status.HTTP_409_CONFLICT,
                )

            for item in items:
                stock = stock_by_isbn[item["isbn"]]
                stock.reserved += item["quantity"]
                stock.save(update_fields=["reserved"])

            reservation = Reservation.objects.create(
                order_reference=order_reference,
                items=items,
            )

        logger.info(
            "stock_reservation_created reservation=%s order=%s",
            reservation.id,
            order_reference,
        )
        return Response(
            ReservationSerializer(reservation).data, status=status.HTTP_201_CREATED
        )


class ReservationDetailView(APIView):
    def get(self, request, pk):
        reservation = get_object_or_404(Reservation, pk=pk)
        return Response(ReservationSerializer(reservation).data)


class ReservationConfirmView(APIView):
    """payment succeeded"""

    def post(self, request, pk):
        reservation = get_object_or_404(Reservation, pk=pk)

        if reservation.status == ReservationStatus.CONFIRMED.value:
            return Response(ReservationSerializer(reservation).data)

        if reservation.status == ReservationStatus.CANCELED.value:
            return Response(
                {"error": "reservation_already_canceled"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            for item in reservation.items:
                stock = StockItem.objects.get(isbn=item["isbn"])
                stock.quantity -= item["quantity"]
                stock.reserved -= item["quantity"]
                stock.save(update_fields=["quantity", "reserved"])

            reservation.status = ReservationStatus.CONFIRMED.value
            reservation.save(update_fields=["status"])

        logger.info("stock_reservation_confirmed reservation=%s", reservation.id)
        return Response(ReservationSerializer(reservation).data)


class ReservationCancelView(APIView):
    """payment failed/expired, so the reserved stock goes back"""

    def post(self, request, pk):
        reservation = get_object_or_404(Reservation, pk=pk)

        if reservation.status == ReservationStatus.CANCELED.value:
            return Response(ReservationSerializer(reservation).data)

        if reservation.status == ReservationStatus.CONFIRMED.value:
            return Response(
                {"error": "reservation_already_confirmed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            for item in reservation.items:
                stock = StockItem.objects.get(isbn=item["isbn"])
                stock.reserved -= item["quantity"]
                stock.save(update_fields=["reserved"])

            reservation.status = ReservationStatus.CANCELED.value
            reservation.save(update_fields=["status"])

        logger.info("stock_reservation_canceled reservation=%s", reservation.id)
        return Response(ReservationSerializer(reservation).data)
