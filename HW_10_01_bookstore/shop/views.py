from django.db.models.aggregates import Avg, Count
from django.db.models import Q
from django.urls import reverse
from django.views.generic import (
    DetailView,
    ListView,
    TemplateView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.shortcuts import get_object_or_404
from shop.models import Author, Book, Category, Rating
from shop.forms import RatingForm
from django.contrib.auth.mixins import LoginRequiredMixin


class MainPageView(TemplateView):
    template_name = "shop/main_page.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["top_books"] = Book.objects.annotate(
            avg_rating=Avg("ratings__rating")
        ).order_by("-avg_rating")[:5]

        context["new_books"] = Book.objects.order_by("-publication_date")[:5]

        context["popular_books"] = Book.objects.annotate(
            ratings_count=Count("ratings")
        ).order_by("-ratings_count")[:5]

        context["top_authors"] = Author.objects.annotate(
            books_count=Count("books")
        ).order_by("-books_count")[:5]

        return context


# def main_page(request):
#     top_books = Book.objects.annotate(avg_rating=Avg("rating__rating")).order_by(
#         "-avg_rating"
#     )[:5]

#     new_books = Book.objects.order_by("-publication_date")[:5]

#     popular_books = Book.objects.annotate(reviews_count=Count("rating")).order_by(
#         "-reviews_count"
#     )[:5]

#     top_authors = Author.objects.annotate(books_count=Count("books")).order_by(
#         "-books_count"
#     )[:5]

#     return render(
#         request,
#         "shop/main_page.html",
#         {
#             "top_books": top_books,
#             "new_books": new_books,
#             "popular_books": popular_books,
#             "top_authors": top_authors,
#         },
#     )


class BooksListView(ListView):
    model = Book
    template_name = "shop/books_list.html"
    context_object_name = "books"
    paginate_by = 5

    def get_queryset(self):
        queryset = super().get_queryset()
        book_query = self.request.GET.get("q", "")
        if book_query:
            queryset = queryset.filter(
                Q(title__icontains=book_query)
                | Q(author__first_name__icontains=book_query)
                | Q(author__last_name__icontains=book_query)
            ).distinct()
        return queryset


# def books_list(request):
# book_query = request.GET.get("q", "")

# books = Book.objects.all()

# if book_query:
#     books = books.filter(
#         Q(title__icontains=book_query)
#         | Q(author__first_name__icontains=book_query)
#         | Q(author__last_name__icontains=book_query)
#     ).distinct()

# paginator = Paginator(books, 5)
# page_number = request.GET.get("page")
# books = paginator.get_page(page_number)

# return render(request, "shop/books_list.html", {"books": books})


# def book_detail(request, book_id):
#     book = Book.objects.get(id=book_id)
#     return render(request, "shop/book_detail.html", {"book": book})


class BookDetailView(DetailView):
    model = Book
    template_name = "shop/book_detail.html"
    context_object_name = "book"


# def authors_list(request):
# author_query = request.GET.get("q", "")

# authors = Author.objects.all()

# if author_query:
#     authors = authors.filter(
#         Q(first_name__icontains=author_query) | Q(last_name__icontains=author_query)
#     )

# paginator = Paginator(authors, 5)
# page_number = request.GET.get("page")
# authors = paginator.get_page(page_number)

# return render(request, "shop/authors_list.html", {"authors": authors})


class AuthorsListView(ListView):
    model = Author
    template_name = "shop/authors_list.html"
    context_object_name = "authors"
    paginate_by = 3

    def get_queryset(self):
        queryset = super().get_queryset()
        author_query = self.request.GET.get("q", "")
        if author_query:
            queryset = queryset.filter(
                Q(first_name__icontains=author_query)
                | Q(last_name__icontains=author_query)
            )
        return queryset


# def author_detail(request, author_id):
#     author = Author.objects.get(id=author_id)
#     return render(request, "shop/author_detail.html", {"author": author})
class AuthorDetailView(DetailView):
    model = Author
    template_name = "shop/author_detail.html"
    context_object_name = "author"


# def categories_list(request):
#     category_query = request.GET.get("q", "")

#     categories = Category.objects.all()

#     if category_query:
#         categories = categories.filter(name__icontains=category_query)

#     paginator = Paginator(categories, 5)
#     page_number = request.GET.get("page")
#     categories = paginator.get_page(page_number)

#     context = {"categories": categories}
#     return render(request, "shop/categories_list.html", context)


class CategoriesListView(ListView):
    model = Category
    template_name = "shop/categories_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        queryset = super().get_queryset()
        category_query = self.request.GET.get("q", "")
        if category_query:
            queryset = queryset.filter(name__icontains=category_query)
        return queryset


class CategoryBooksListView(ListView):
    model = Book
    template_name = "shop/category_detail.html"
    context_object_name = "books"
    paginate_by = 3

    def get_queryset(self):
        return Book.objects.filter(category__pk=self.kwargs["pk"]).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = Category.objects.get(pk=self.kwargs["pk"])
        return context


# def add_review(request, book_id):
#     book = Book.objects.get(id=book_id)

#     if request.method == "POST":
#         rating_value = int(request.POST.get("rating"))
#         review_text = request.POST.get("review")

#         rating = Rating.objects.create(
#             book=book, user=request.user, rating=rating_value
#         )

#         avg_rating = Rating.objects.filter(book=book).aggregate(Avg("rating"))[
#             "rating__avg"
#         ]
#         book.calculated_avg_rating = avg_rating
#         book.save()

#     return render(request, "shop/book_detail.html", {"book": book})


class AddFeedbackView(LoginRequiredMixin, CreateView):
    model = Rating
    form_class = RatingForm
    template_name = "shop/add_feedback.html"
    login_url = "user_management:login"

    def form_valid(self, form):
        book = get_object_or_404(Book, pk=self.kwargs["pk"])

        form.instance.book = book
        form.instance.user = self.request.user

        response = super().form_valid(form)

        book.calculated_avg_rating = Rating.objects.filter(book=book).aggregate(
            Avg("rating")
        )["rating__avg"]
        book.save()

        return response

    def get_success_url(self):
        return reverse("shop:book_detail", kwargs={"pk": self.kwargs["pk"]})


class UpdateFeedbackView(LoginRequiredMixin, UpdateView):
    model = Rating
    form_class = RatingForm
    template_name = "shop/update_feedback.html"
    login_url = "user_management:login"

    def get_queryset(self):
        return Rating.objects.filter(user=self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)

        book = self.object.book
        avg_rating = Rating.objects.filter(book=book).aggregate(Avg("rating"))[
            "rating__avg"
        ]
        book.calculated_avg_rating = avg_rating
        book.save()

        return response

    def get_success_url(self):
        return reverse(
            "shop:book_detail",
            kwargs={"pk": self.object.book.pk},
        )


class DeleteFeedbackView(LoginRequiredMixin, DeleteView):
    model = Rating
    template_name = "shop/delete_feedback.html"
    login_url = "user_management:login"

    def get_queryset(self):
        return Rating.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        book = self.object.book

        response = super().delete(request, *args, **kwargs)

        avg = Rating.objects.filter(book=book).aggregate(Avg("rating"))["rating__avg"]

        book.calculated_avg_rating = avg or 0
        book.save()

        return response

    def get_success_url(self):
        return reverse(
            "shop:book_detail",
            kwargs={"pk": self.object.book.pk},
        )
