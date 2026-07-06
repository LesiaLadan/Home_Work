from django.db import models
from django.conf import settings


class Publisher(models.Model):
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=200)
    website = models.URLField()

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Publisher: {self.name}, City: {self.city}, " f"Website: {self.website}"


class Author(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    biography = models.TextField(blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ManyToManyField(Author, related_name="books")
    isbn = models.CharField(max_length=13, unique=True)
    publication_date = models.DateField()
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
    added_date = models.DateTimeField(auto_now_add=True)
    in_stock = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    language = models.CharField(max_length=50)
    category = models.ManyToManyField(Category, related_name="books")
    calculated_avg_rating = models.DecimalField(max_digits=3, decimal_places=2)
    description = models.TextField(blank=True)

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
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ratings",
    )
    rating = models.PositiveIntegerField()
    feedback = models.TextField(blank=True)

    def __str__(self):
        return f"{self.book.title} - {self.user.username}"
