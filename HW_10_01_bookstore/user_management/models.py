from django.db import models

from django.contrib.auth.models import AbstractUser

from book_store import settings


class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True)
    birth_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.get_full_name() or self.username


class DeliveryAddress(models.Model):
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    street = models.CharField(max_length=200)
    branch = models.CharField(max_length=100, blank=True, null=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.owner.username} - {self.city}, {self.street}, {self.postal_code}"


class LastViewedBooks(models.Model):
    book = models.ForeignKey("shop.Book", on_delete=models.CASCADE)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-viewed_at"]
        unique_together = ("book", "owner")

    def __str__(self):
        return f"{self.owner.username} - {self.book.title}"
