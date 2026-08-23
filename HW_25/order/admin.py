from django.contrib import admin
from order.models import Order, OrderDetails


class OrderDetailsInline(admin.TabularInline):
    model = OrderDetails
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "owner",
        "order_date",
        "status",
        "total_price",
        "payment_method",
        "payment_status",
        "ttn",
        "free_shipping",
    )
    search_fields = ("owner__email", "owner__username")
    list_filter = ("status", "payment_status", "order_date")
    inlines = [OrderDetailsInline]

    @admin.display(boolean=True, description="Free Shipping")
    def free_shipping(self, obj):
        return obj.total_price >= 500


@admin.register(OrderDetails)
class OrderDetailsAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "book",
        "quantity",
        "price",
    )
    search_fields = (
        "order__id",
        "book__title",
    )
    list_filter = (
        "order__status",
        "order__payment_status",
    )