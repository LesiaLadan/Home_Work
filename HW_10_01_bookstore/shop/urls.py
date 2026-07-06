from django.urls import path
from .views import AuthorDetailView, AuthorsListView, CategoriesListView, CategoryBooksListView, DeleteFeedbackView, MainPageView, BooksListView, BookDetailView, AddFeedbackView, UpdateFeedbackView

app_name = "shop"

urlpatterns = [
    path("", MainPageView.as_view(), name="main_page"),
    path("books/", BooksListView.as_view(), name="books_list"),
    path("books/<int:pk>/", BookDetailView.as_view(), name="book_detail"),
    path("authors/", AuthorsListView.as_view(), name="authors_list"),
    path("authors/<int:pk>/", AuthorDetailView.as_view(), name="author_detail"),
    path("categories/", CategoriesListView.as_view(), name="categories_list"),
    path("category/<int:pk>/", CategoryBooksListView.as_view(), name="category_detail"),
    path("add_feedback/<int:pk>/", AddFeedbackView.as_view(), name="add_feedback"),
    path("feedback/<int:pk>/edit/", UpdateFeedbackView.as_view(), name="update_feedback"),
    path("feedback/<int:pk>/delete/", DeleteFeedbackView.as_view(), name="delete_feedback"),
]
