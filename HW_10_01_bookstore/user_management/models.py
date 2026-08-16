from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy

from book_store import settings


class User(AbstractUser):
    phone = models.CharField(
        gettext_lazy("Phone"),
        max_length=20,
        blank=True,
    )
    birth_date = models.DateField(
        gettext_lazy("Birth date"),
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.get_full_name() or self.username


class DeliveryAddress(models.Model):
    postal_code = models.CharField(
        gettext_lazy("Postal code"),
        max_length=20,
    )
    city = models.CharField(
        gettext_lazy("City"),
        max_length=100,
    )
    street = models.CharField(
        gettext_lazy("Street"),
        max_length=200,
    )
    branch = models.CharField(
        gettext_lazy("Nova Poshta branch"),
        max_length=100,
        blank=True,
        null=True,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy("Owner"),
    )

    def __str__(self):
        return f"{self.owner.username} - {self.city}, {self.street}, {self.postal_code}"


class LastViewedBooks(models.Model):
    book = models.ForeignKey(
        "shop.Book",
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy("Book"),
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy("Owner"),
    )
    viewed_at = models.DateTimeField(
        gettext_lazy("Viewed at"),
        auto_now=True,
    )

    class Meta:
        ordering = ["-viewed_at"]
        unique_together = ("book", "owner")

    def __str__(self):
        return f"{self.owner.username} - {self.book.title}"
