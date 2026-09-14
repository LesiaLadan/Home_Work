from user_management.models import LastViewedBooks
from shop.models import Book


class LastViewedBooksMiddleware:
    """Tracks the last viewed books for authenticated users"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated and request.path.startswith("/books/"):
            try:
                book_id = request.path.strip("/").split("/")[-1]
                book = Book.objects.get(pk=book_id)

                LastViewedBooks.objects.update_or_create(
                    owner=request.user,
                    book=book,
                )

            except (Book.DoesNotExist, ValueError):
                pass

        return response
