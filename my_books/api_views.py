# my_books/api_views.py
#
# Your normal views return HTML pages (render(...)).
# API views return DATA (JSON) and use HTTP status codes to say what happened.
#
#   GET     read          200 OK
#   POST    create        201 Created
#   PUT     replace all   200 OK
#   PATCH   change a bit  200 OK
#   DELETE  remove        204 No Content

from django.db.models import Q
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.reverse import reverse

from .models import Book, Categories
from .permissions import IsOwnerOrStaffOrReadOnly
from .serializers import BookSerializer, CategorySerializer
from .views import with_categories   # reuse the helper from your website views


# --- 1. A function-based API view (DRF tutorial, part 2) -----------------

@api_view(['GET'])
def api_root(request, format=None):
    """The front door of the API: links to everything else."""
    return Response({
        'books': reverse('api:book-list', request=request, format=format),
        'categories': reverse('api:category-list', request=request, format=format),
        'token': reverse('api:token', request=request, format=format),
    })


# --- 2. Class-based API views (DRF tutorial, part 3) ----------------------
# ListCreateAPIView already knows how to do
#     GET  /api/books/   -> list
#     POST /api/books/   -> create
class BookListCreate(generics.ListCreateAPIView):
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]   # read: anyone, write: logged in

    def get_queryset(self):
        books = with_categories(Book.published).order_by('-created')

        # /api/books/?q=habits   (the same search as your website)
        query = self.request.query_params.get('q', '').strip()
        if query:
            books = books.filter(
                Q(title__icontains=query)
                | Q(author__icontains=query)
                | Q(description__icontains=query)
            )

        # /api/books/?category=3   (only books in category 3)
        category = self.request.query_params.get('category', '')
        if category.isdigit():
            books = books.filter(categories__id=int(category))
        return books

    def perform_create(self, serializer):
        # The client never sends "added_by", the server knows who is logged in.
        serializer.save(added_by=self.request.user)


# RetrieveUpdateDestroyAPIView does
#     GET /api/books/<slug>/      -> one book
#     PUT / PATCH                 -> update
#     DELETE                      -> delete
class BookDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrStaffOrReadOnly]
    lookup_field = 'slug'     # find the book by slug, like your website URLs do

    def get_queryset(self):
        return with_categories(Book.published.select_related('added_by') )


class CategoryList(generics.ListAPIView):
    queryset = Categories.objects.order_by('name')
    serializer_class = CategorySerializer
    pagination_class = None   # only a few categories, no need for pages
