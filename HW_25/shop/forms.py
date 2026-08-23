from django import forms
from django.utils.translation import gettext_lazy

from shop.models import Rating


class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ["rating", "feedback"]
        labels = {
            "rating": gettext_lazy("Rating"),
            "feedback": gettext_lazy("Feedback"),
        }