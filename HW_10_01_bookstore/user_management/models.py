from django.db import models


class DeliveryAddress(models.Model):
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    street = models.CharField(max_length=200)
    branch = models.CharField(max_length=100, blank=True, null=True)
    owner = models.ForeignKey("auth.User", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.owner.username} - {self.city}, {self.street}, {self.postal_code}"


class LastViewedBooks(models.Model):
    book = models.ForeignKey("shop.Book", on_delete=models.CASCADE)
    owner = models.ForeignKey("auth.User", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.owner.username} - {self.book.title}"
