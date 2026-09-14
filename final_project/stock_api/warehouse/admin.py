from django.contrib import admin

from .models import Reservation, StockItem


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ("isbn", "title", "quantity", "reserved", "available")
    search_fields = ("isbn", "title")


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("id", "order_reference", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("id", "order_reference", "status", "items", "created_at")

    def has_add_permission(self, request):
        return False
