
# my_books/urls.py
from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

app_name = 'my_books'

urlpatterns = [

    # Home
    path('', views.home_page, name='index'),

    # Authentication
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', views.register_view, name='register'),

    # Books
    path('books/', views.BookListView.as_view(), name='book_list'),
    path('books/add/', views.add_book_view, name='add_book'),
    path('books/<slug:slug>/', views.book_detail_view, name='book_detail'),
    path('books/<slug:slug>/edit/', views.edit_book_view, name='edit_book'),
    path('books/<slug:slug>/share/', views.share_book_view, name='share_book'),

    # Categories
    path('category/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),
]

