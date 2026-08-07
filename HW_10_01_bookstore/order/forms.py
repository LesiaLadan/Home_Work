from django import forms
from order.models import PaymentMethod
from user_management.models import DeliveryAddress


class DeliveryAddressForm(forms.ModelForm):
    payment_method = forms.ChoiceField(
        label="Payment Method",
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
            "postal_code": "Postal Code",
            "city": "City",
            "street": "Street",
            "branch": "Nova Poshta Branch",
        }

        widgets = {
            "postal_code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Postal code",
                }
            ),
            "city": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "City",
                }
            ),
            "street": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Street",
                }
            ),
            "branch": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nova Poshta branch (optional)",
                }
            ),
        }