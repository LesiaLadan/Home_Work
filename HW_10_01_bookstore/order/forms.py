from django import forms
from django.utils.translation import gettext_lazy

from order.models import PaymentMethod
from user_management.models import DeliveryAddress


class DeliveryAddressForm(forms.ModelForm):
    payment_method = forms.ChoiceField(
        label=gettext_lazy("Payment Method"),
        choices=[(item.value, item.name.title()) for item in PaymentMethod],
        widget=forms.RadioSelect,
    )

    class Meta:
        model = DeliveryAddress
        fields = (
            "postal_code",
            "city",
            "street",
            "branch",
        )

        labels = {
            "postal_code": gettext_lazy("Postal Code"),
            "city": gettext_lazy("City"),
            "street": gettext_lazy("Street"),
            "branch": gettext_lazy("Nova Poshta Branch"),
        }

        widgets = {
            "postal_code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": gettext_lazy("Postal code"),
                }
            ),
            "city": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": gettext_lazy("City"),
                }
            ),
            "street": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": gettext_lazy("Street"),
                }
            ),
            "branch": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": gettext_lazy(
                        "Nova Poshta branch (optional)"
                    ),
                }
            ),
        }