import asyncio

from asgiref.sync import sync_to_async
from django.db.models.aggregates import Avg, Count
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
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
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache

from user_management.models import LastViewedBooks, User
import structlog

logger = structlog.get_logger(__name__)

HOMEPAGE_LIST_LIMIT = 5


async def _get_top_books() -> list[Book]:
    """Top-rated books (average rating, at least one rating), with author/category prefetched."""
    queryset = (
        Book.objects.annotate(
            avg_rating=Avg("ratings__rating"),
            ratings_count=Count("ratings"),
        )
        .filter(ratings_count__gt=0)
        .order_by("-avg_rating")
        .prefetch_related("author", "category")[:HOMEPAGE_LIST_LIMIT]
    )
    return [book async for book in queryset]


async def _get_new_books() -> list[Book]:
    """Most recently published books, with author/category prefetched."""
    queryset = Book.objects.order_by("-publication_date").prefetch_related(
        "author", "category"
    )[:HOMEPAGE_LIST_LIMIT]
    return [book async for book in queryset]


async def _get_popular_books() -> list[Book]:
    """Most-rated (by number of ratings) books, with author/category prefetched."""
    queryset = (
        Book.objects.annotate(ratings_count=Count("ratings"))
        .order_by("-ratings_count")
        .prefetch_related("author", "category")[:HOMEPAGE_LIST_LIMIT]
    )
    return [book async for book in queryset]


async def _get_top_authors() -> list[Author]:
    """Authors with the most books."""
    queryset = Author.objects.annotate(books_count=Count("books")).order_by(
        "-books_count"
    )[:HOMEPAGE_LIST_LIMIT]
    return [author async for author in queryset]


async def _get_last_viewed(user: User) -> list[LastViewedBooks]:
    """The current user's most recently viewed books, or an empty list if anonymous."""
    if not user.is_authenticated:
        return []
    queryset = (
        LastViewedBooks.objects.filter(owner=user)
        .select_related("book")
        .order_by("-viewed_at")[:HOMEPAGE_LIST_LIMIT]
    )
    return [viewed_book async for viewed_book in queryset]


class MainPageView(View):
    """Home page: top-rated, newest, and most-popular books, top authors, and recently viewed."""

    template_name = "shop/main_page.html"

    async def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Gather all homepage sections concurrently and render the page.

        The five sections are independent of each other, so they are
        fetched with ``asyncio.gather`` instead of sequentially to keep
        total page latency close to the slowest single query rather than
        the sum of all of them.
        """
        try:
            top_books, new_books, popular_books, top_authors, last_viewed = (
                await asyncio.gather(
                    _get_top_books(),
                    _get_new_books(),
                    _get_popular_books(),
                    _get_top_authors(),
                    _get_last_viewed(request.user),
                )
            )
        except Exception:
            logger.exception("Failed to load main page data")
            raise

        context = {
            "top_books": top_books,
            "new_books": new_books,
            "popular_books": popular_books,
            "top_authors": top_authors,
            "last_viewed": last_viewed,
        }
        logger.info("Main page loaded", authenticated=request.user.is_authenticated)
        return await sync_to_async(render)(request, self.template_name, context)


class BooksListView(ListView):
    """Paginated list of books, optionally filtered by a title/author search query."""

    model = Book
    template_name = "shop/books_list.html"
    context_object_name = "books"
    paginate_by = 5

    def get_queryset(self):
        """Return all books (with authors prefetched), filtered by ``?q=`` if present.

        The query matches against book title, author first name, and author
        last name (case-insensitive, partial match).
        """
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
    """Single book's detail page."""

    model = Book
    template_name = "shop/book_detail.html"
    context_object_name = "book"

    def get_object(self, queryset=None):
        """Fetch the book and log that its detail page was opened."""

        cache_key = f"book_detail_{self.kwargs['pk']}"
        book = cache.get(cache_key)

        if book is None:
            book = super().get_object(queryset)
            cache.set(cache_key, book, 60 * 15)

        logger.info(
            "Book detail opened",
            book_id=book.id,
            title=book.title,
        )

        return book


@method_decorator(cache_page(60 * 15), name="dispatch")
class AuthorsListView(ListView):
    """Paginated list of authors, optionally filtered by a name search query."""

    model = Author
    template_name = "shop/authors_list.html"
    context_object_name = "authors"
    paginate_by = 3

    def get_queryset(self):
        """Return all authors, filtered by ``?q=`` against first/last name if present."""
        queryset = super().get_queryset()
        author_query = self.request.GET.get("q", "")
        if author_query:
            queryset = queryset.filter(
                Q(first_name__icontains=author_query)
                | Q(last_name__icontains=author_query)
            )
            logger.info(
                "Found authors matching query",
                author_count=queryset.count(),
                query=author_query,
            )
        return queryset


@method_decorator(cache_page(60 * 15), name="dispatch")
class AuthorDetailView(DetailView):
    """Single author's detail page."""

    model = Author
    template_name = "shop/author_detail.html"
    context_object_name = "author"

    def get_object(self, queryset=None):
        """Fetch the author and log that its detail page was opened."""
        author = super().get_object(queryset)
        logger.info(
            "Author detail opened",
            author_id=author.id,
            author=str(author),
        )
        return author


@method_decorator(cache_page(60 * 15), name="dispatch")
class CategoriesListView(ListView):
    """List of all book categories, optionally filtered by a name search query."""

    model = Category
    template_name = "shop/categories_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        """Return all categories, filtered by ``?q=`` against the name if present."""
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
    """Paginated list of books belonging to a single category."""

    model = Book
    template_name = "shop/category_detail.html"
    context_object_name = "books"
    paginate_by = 3

    def get_queryset(self):
        """Return the books in the category identified by the ``pk`` URL kwarg."""
        queryset = Book.objects.filter(category__pk=self.kwargs["pk"]).distinct()
        logger.info(
            "Loading books for category",
            category_id=self.kwargs["pk"],
            books_count=queryset.count(),
        )
        return queryset

    def get_context_data(self, **kwargs):
        """Add the current ``Category`` instance to the template context."""
        logger.info("Loading context data for category", category_id=self.kwargs["pk"])
        context = super().get_context_data(**kwargs)
        context["category"] = Category.objects.get(pk=self.kwargs["pk"])
        return context


class AddFeedbackView(LoginRequiredMixin, CreateView):
    """Submit a new rating/feedback for a book and recalculate its average rating."""

    model = Rating
    form_class = RatingForm
    template_name = "shop/add_feedback.html"
    login_url = "user_management:login"

    def form_valid(self, form):
        """Attach the target book and current user to the rating, then save it.

        After the ``Rating`` is created, recomputes ``Book.calculated_avg_rating``
        from all ratings for that book.
        """
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
        """Redirect back to the book's detail page after a successful submission."""
        return reverse("shop:book_detail", kwargs={"pk": self.kwargs["pk"]})


class UpdateFeedbackView(LoginRequiredMixin, UpdateView):
    """Edit the current user's own rating/feedback and recalculate the book's average rating."""

    model = Rating
    form_class = RatingForm
    template_name = "shop/update_feedback.html"
    login_url = "user_management:login"

    def get_queryset(self):
        """Restrict editable ratings to those owned by the current user."""
        return Rating.objects.filter(user=self.request.user)

    def form_valid(self, form):
        """Save the updated rating, then recompute ``Book.calculated_avg_rating``."""
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
        """Redirect back to the book's detail page after a successful update."""
        return reverse(
            "shop:book_detail",
            kwargs={"pk": self.object.book.pk},
        )


class DeleteFeedbackView(LoginRequiredMixin, DeleteView):
    """Delete the current user's own rating/feedback and recalculate the book's average rating."""

    model = Rating
    template_name = "shop/delete_feedback.html"
    login_url = "user_management:login"

    def get_queryset(self):
        """Restrict deletable ratings to those owned by the current user."""
        return Rating.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        """Delete the rating, then recompute ``Book.calculated_avg_rating`` (0 if none remain)."""
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
        """Redirect back to the book's detail page after a successful deletion."""
        return reverse(
            "shop:book_detail",
            kwargs={"pk": self.object.book.pk},
        )
