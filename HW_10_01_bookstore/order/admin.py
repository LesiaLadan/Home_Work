from django.contrib import admin
from order.models import Order, OrderDetails


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
    search_fields = ("owner", "status")
    list_filter = ("status", "payment_status", "order_date")

    def free_shipping(self, obj):
        return obj.total_price >= 500

    free_shipping.boolean = True
    free_shipping.short_description = "Free Shipping"


class OrderDetailsAdmin(admin.ModelAdmin):
    list_display = (
        "order__id",
        "book__title",
        "book__isbn",
        "quantity",
        "price",
        "order__owner",
    )
    search_fields = ("order__id", "book__title")
    list_filter = ("order__id", "order__status")


admin.site.register(Order, OrderAdmin)
admin.site.register(OrderDetails, OrderDetailsAdmin)
