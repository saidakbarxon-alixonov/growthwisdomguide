# my_books/api_urls.py
from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from . import api_views

app_name = 'api'

urlpatterns = [
    path('', api_views.api_root, name='root'),
    path('books/', api_views.BookListCreate.as_view(), name='book-list'),
    path('books/<slug:slug>/', api_views.BookDetail.as_view(), name='book-detail'),
    path('categories/', api_views.CategoryList.as_view(), name='category-list'),

    # POST username + password here -> you get a token back (your "API key")
    path('token/', obtain_auth_token, name='token'),
]
