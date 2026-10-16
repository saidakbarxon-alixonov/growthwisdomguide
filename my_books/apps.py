from django.apps import AppConfig


class MyBooksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'my_books'
    verbose_name = 'Book Management & Library'
