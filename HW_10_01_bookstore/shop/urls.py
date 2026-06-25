from django.urls import path, include


from .views import main_page, books_list, book_detail, authors_list, author_detail  

urlpatterns = [
    path("", main_page, name="main_page"),
    path("books/", books_list, name="books_list"),
    path("books/<int:book_id>/", book_detail, name="book_detail"),
    path("authors/", authors_list, name="authors_list"),
    path("authors/<int:author_id>/", author_detail, name="author_detail"),
    path("orders/", include("order.urls")),
]
