from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy


class Publisher(models.Model):
    name = models.CharField(
        gettext_lazy("Name"),
        max_length=100,
    )
    city = models.CharField(
        gettext_lazy("City"),
        max_length=200,
    )
    website = models.URLField(
        gettext_lazy("Website"),
    )

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Publisher: {self.name}, City: {self.city}, " f"Website: {self.website}"


class Author(models.Model):
    first_name = models.CharField(
        gettext_lazy("First name"),
        max_length=50,
    )
    last_name = models.CharField(
        gettext_lazy("Last name"),
        max_length=50,
    )
    biography = models.TextField(
        gettext_lazy("Biography"),
        blank=True,
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Category(models.Model):
    name = models.CharField(
        gettext_lazy("Name"),
        max_length=100,
    )

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(
        gettext_lazy("Title"),
        max_length=200,
    )
    author = models.ManyToManyField(
        Author,
        related_name="books",
        verbose_name=gettext_lazy("Author"),
    )
    isbn = models.CharField(
        gettext_lazy("ISBN"),
        max_length=13,
        unique=True,
    )
    publication_date = models.DateField(
        gettext_lazy("Publication date"),
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.CASCADE,
        verbose_name=gettext_lazy("Publisher"),
    )
    added_date = models.DateTimeField(
        gettext_lazy("Added date"),
        auto_now_add=True,
    )
    in_stock = models.PositiveIntegerField(
        gettext_lazy("In stock"),
    )
    price = models.DecimalField(
        gettext_lazy("Price"),
        max_digits=6,
        decimal_places=2,
    )
    wholesale_price = models.DecimalField(
        gettext_lazy("Wholesale price"),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )
    language = models.CharField(
        gettext_lazy("Language"),
        max_length=50,
    )
    category = models.ManyToManyField(
        Category,
        related_name="books",
        verbose_name=gettext_lazy("Category"),
    )
    calculated_avg_rating = models.DecimalField(
        gettext_lazy("Calculated average rating"),
        max_digits=3,
        decimal_places=2,
    )
    description = models.TextField(
        gettext_lazy("Description"),
        blank=True,
    )

    class Meta:
        permissions = [
            (
                "view_wholesale_price",
                gettext_lazy("Can view wholesale price"),
            ),
        ]

    def __str__(self):
        authors = ", ".join(str(author) for author in self.author.all())
        return f"{self.title} by {authors}"

    def __repr__(self):
        authors = ", ".join(str(author) for author in self.author.all())
        return f"{self.title} by {authors}"


class Rating(models.Model):
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="ratings",
        verbose_name=gettext_lazy("Book"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ratings",
        verbose_name=gettext_lazy("User"),
    )
    rating = models.PositiveIntegerField(
        gettext_lazy("Rating"),
    )
    feedback = models.TextField(
        gettext_lazy("Feedback"),
        blank=True,
    )

    def __str__(self):
        return f"{self.book.title} - {self.user.username}"