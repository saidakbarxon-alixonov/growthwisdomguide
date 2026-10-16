from django.db.models import Count, Q

from .models import Categories


def categories(request):
    """Makes `categories` available in every template (needed by the sidebar).

    Registered in settings.py -> TEMPLATES -> context_processors.
    `book_count` only counts published books.
    """
    return {
        'categories': Categories.objects.annotate(
            book_count=Count('books', filter=Q(books__status='published'))
        ).order_by('name')
    }
