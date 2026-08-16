from asgiref.sync import sync_to_async
from django.db.models.aggregates import Avg, Count
from django.db.models import Q
from django.urls import reverse
from django.views.generic import (
    DetailView,
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
    View,
)
from django.shortcuts import get_object_or_404, render
from shop.models import Author, Book, Category, Rating
from shop.forms import RatingForm
from django.contrib.auth.mixins import LoginRequiredMixin

from user_management.models import LastViewedBooks
import structlog

logger = structlog.get_logger(__name__)


class MainPageView(View):
    template_name = "shop/main_page.html"

    async def get(self, request, *args, **kwargs):
        top_books = [
            book
            async for book in (
                Book.objects.annotate(
                    avg_rating=Avg("ratings__rating"),
                    ratings_count=Count("ratings"),
                )
                .filter(ratings_count__gt=0)
                .order_by("-avg_rating")[:5]
            )
        ]
        new_books = [
            book async for book in Book.objects.order_by("-publication_date")[:5]
        ]

        popular_books = [
            book
            async for book in (
                Book.objects.annotate(ratings_count=Count("ratings")).order_by(
                    "-ratings_count"
                )[:5]
            )
        ]

        top_authors = [
            author
            async for author in (
                Author.objects.annotate(books_count=Count("books")).order_by(
                    "-books_count"
                )[:5]
            )
        ]

        last_viewed = []
        if request.user.is_authenticated:
            last_viewed = [
                viewed_book
                async for viewed_book in (
                    LastViewedBooks.objects.filter(owner=request.user)
                    .select_related("book")
                    .order_by("-viewed_at")[:5]
                )
            ]
        context = {
            "top_books": top_books,
            "new_books": new_books,
            "popular_books": popular_books,
            "top_authors": top_authors,
            "last_viewed": last_viewed,
        }
        logger.info("Main page loaded")
        return await sync_to_async(render)(request, self.template_name, context)


class BooksListView(ListView):
    model = Book
    template_name = "shop/books_list.html"
    context_object_name = "books"
    paginate_by = 5

    def get_queryset(self):
        queryset = super().get_queryset().prefetch_related("author")

        book_query = self.request.GET.get("q", "")

        if book_query:
            queryset = queryset.filter(
                Q(title__icontains=book_query)
                | Q(author__first_name__icontains=book_query)
                | Q(author__last_name__icontains=book_query)
            ).distinct()
            logger.info(
                "Books search",
                query=book_query,
                results=queryset.count(),
            )
        return queryset


class BookDetailView(DetailView):
    model = Book
    template_name = "shop/book_detail.html"
    context_object_name = "book"

    def get_object(self, queryset=None):
        book = super().get_object(queryset)
        logger.info(
            "Book detail opened",
            book_id=book.id,
            title=book.title,
        )

        return book


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
                Q(first_name__icontains=author_query) | Q(last_name__icontains=author_query)
            )
            logger.info(
                "Found authors matching query",
                author_count=queryset.count(),
                query=author_query,
            )
        return queryset


class AuthorDetailView(DetailView):
    model = Author
    template_name = "shop/author_detail.html"
    context_object_name = "author"

    def get_object(self, queryset=None):
        author = super().get_object(queryset)
        logger.info(
            "Author detail opened",
            author_id=author.id,
            author=str(author),
        )
        return author


class CategoriesListView(ListView):
    model = Category
    template_name = "shop/categories_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        queryset = super().get_queryset()
        category_query = self.request.GET.get("q", "")
        if category_query:
            queryset = queryset.filter(name__icontains=category_query)
            logger.info(
                "Found categories matching query",
                category_count=queryset.count(),
                query=category_query,
            )
        return queryset


class CategoryBooksListView(ListView):
    model = Book
    template_name = "shop/category_detail.html"
    context_object_name = "books"
    paginate_by = 3

    def get_queryset(self):
        queryset = Book.objects.filter(category__pk=self.kwargs["pk"]).distinct()
        logger.info(
            "Loading books for category",
            category_id=self.kwargs["pk"],
            books_count=queryset.count(),
        )
        return queryset

    def get_context_data(self, **kwargs):
        logger.info("Loading context data for category", category_id=self.kwargs["pk"])
        context = super().get_context_data(**kwargs)
        context["category"] = Category.objects.get(pk=self.kwargs["pk"])
        return context


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
        logger.info(
            "Feedback created",
            book_id=book.id,
            username=self.request.user.username,
        )

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
        logger.info(
            "Feedback updated",
            book_id=book.id,
            user=self.request.user.username,
            average_rating=avg_rating,
        )

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
        logger.info(
            "Feedback deleted",
            book_id=book.id,
            user=self.request.user.username,
        )
        return response

    def get_success_url(self):
        return reverse(
            "shop:book_detail",
            kwargs={"pk": self.object.book.pk},
        )
