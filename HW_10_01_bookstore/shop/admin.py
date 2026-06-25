from decimal import Decimal

from django.contrib import admin
import shop.models as shop_models
from django.db.models import F


class PublisherAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "website")
    search_fields = ("name", "city")
    list_filter = ("city",)


class AuthorAdmin(admin.ModelAdmin):
    list_display = ("last_name", "first_name", "get_books")
    search_fields = ("last_name",)

    def get_books(self, obj):
        return ", ".join(book.title for book in obj.books.all())

    get_books.short_description = "Books"


class BookAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "get_authors",
        "isbn",
        "price",
        "in_stock",
        "publication_date",
        "publisher",
    )

    search_fields = ("title", "isbn")
    list_filter = ("publication_date", "publisher")
    actions = ["increase_price_10", "decrease_price_10"]

    def increase_price_10(self, request, queryset):
        queryset.update(price=F("price") * Decimal("1.1"))

    def decrease_price_10(self, request, queryset):
        queryset.update(price=F("price") * Decimal("0.9"))

    increase_price_10.short_description = "Increase Price by 10"
    decrease_price_10.short_description = "Decrease Price by 10"

    def get_authors(self, obj):
        return ", ".join(f"{a.first_name} {a.last_name}" for a in obj.author.all())

    get_authors.short_description = "Authors"


class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


class RatingAdmin(admin.ModelAdmin):
    list_display = ("book", "user", "rating", "feedback")
    search_fields = ("book__title", "user__username")
    list_filter = ("rating",)


admin.site.register(shop_models.Book, BookAdmin)
admin.site.register(shop_models.Author, AuthorAdmin)
admin.site.register(shop_models.Publisher, PublisherAdmin)
admin.site.register(shop_models.Category, CategoryAdmin)
admin.site.register(shop_models.Rating, RatingAdmin)
