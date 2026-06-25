from django.db.models.aggregates import Avg, Count

from django.shortcuts import render
from django.db.models import Q

from shop.models import Author, Book


def main_page(request):
    top_books = Book.objects.annotate(avg_rating=Avg("rating__rating")).order_by(
        "-avg_rating"
    )[:5]

    new_books = Book.objects.order_by("-publication_date")[:5]

    popular_books = Book.objects.annotate(reviews_count=Count("rating")).order_by(
        "-reviews_count"
    )[:5]

    top_authors = Author.objects.annotate(books_count=Count("books")).order_by(
        "-books_count"
    )[:5]

    return render(
        request,
        "shop/main_page.html",
        {
            "top_books": top_books,
            "new_books": new_books,
            "popular_books": popular_books,
            "top_authors": top_authors,
        },
    )


# def books_list(request):
#     books = Book.objects.all()
#     return render(request, "shop/books_list.html", {"books": books})


def books_list(request):
    query = request.GET.get("q")

    books = Book.objects.all()

    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__first_name__icontains=query) |
            Q(author__last_name__icontains=query)
        )

    return render(request, "shop/books_list.html", {
        "books": books
    })


def book_detail(request, book_id):
    book = Book.objects.get(id=book_id)
    return render(request, "shop/book_detail.html", {"book": book})


def authors_list(request):
    authors = Author.objects.all()
    return render(request, "shop/authors_list.html", {"authors": authors})


def author_detail(request, author_id):
    author = Author.objects.get(id=author_id)
    return render(request, "shop/author_detail.html", {"author": author})
