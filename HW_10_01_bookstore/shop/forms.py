from django import forms
from shop.models import Rating


class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ["rating", "feedback"]
