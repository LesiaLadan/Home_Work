from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from shop.models import Book, Rating

FRAGMENT_NAMES = [
    "top_books_fragment",
    "new_books_fragment",
    "popular_books_fragment",
    "top_authors_fragment",
]


def invalidate_main_page_fragments():
    for name in FRAGMENT_NAMES:
        cache.delete(make_template_fragment_key(name))


@receiver(post_save, sender=Book)
@receiver(post_delete, sender=Book)
def invalidate_book_cache(sender, instance, **kwargs):
    cache.delete(f"book_detail_{instance.pk}")
    invalidate_main_page_fragments()


@receiver(post_save, sender=Rating)
@receiver(post_delete, sender=Rating)
def invalidate_fragments_on_rating_change(sender, instance, **kwargs):
    invalidate_main_page_fragments()
