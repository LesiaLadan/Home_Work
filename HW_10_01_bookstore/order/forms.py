from django import forms
from order.models import Order, OrderDetails


class NewOrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = (
            "owner",
            "status",
            "total_price",
            "payment_method",
            "payment_status",
            "ttn",
        )


class NewOrderDetailsForm(forms.ModelForm):
    class Meta:
        model = OrderDetails
        fields = (
            "order",
            "book",
            "quantity",
            "price",
        )
