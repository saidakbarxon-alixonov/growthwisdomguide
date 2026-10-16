from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.contrib.auth.models import User

# Create your models here.

class PublishedManager(models.Manager):

    def get_queryset(self):

        return super().get_queryset().filter(status='published')


class Categories(models.Model):

    name = models.CharField(
        max_length=100, unique=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        # The page that lists every book in this category.
        return reverse("my_books:category_detail", kwargs={"pk": self.pk})

    class Meta:
        verbose_name_plural = "Categories"

class Status(models.TextChoices):

    DRAFT = 'draft', 'Draft'
    PUBLISHED = 'published', 'Published'


class Book(models.Model):

    slug = models.SlugField(
        max_length=100, unique=True, db_index=True, blank=True, help_text="e.g. atomic-habits")
    title = models.CharField(
        max_length=200)
    author = models.CharField(
        max_length=200)
    description = models.TextField(
        blank=True)
    categories = models.ManyToManyField(
        Categories, related_name="books", blank=True)

    added_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="added_books")
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PUBLISHED, db_index=True)
    created = models.DateTimeField(
        auto_now_add=True)
    updated = models.DateTimeField(
        auto_now=True)

    objects = models.Manager()
    published = PublishedManager()


    class Meta:
        verbose_name_plural = "Books"


    def save(self, *args, **kwargs):

        if not self.slug:
            base_slug = slugify(self.title)[:90]
            slug = base_slug

            counter = 1

            while Book.objects.filter(
                    slug=slug
            ).exists():

                slug = f'{base_slug}-{counter}'
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} by {self.author}"

    def get_absolute_url(self):
        return reverse("my_books:book_detail", kwargs={"slug": self.slug})

    @property
    def primary_category(self):
        """The first category of the book (or None). Used to pick the card colour.

        Uses .all() so it reuses the categories the view already loaded
        with prefetch_related, instead of asking the database again.
        """
        categories = list(self.categories.all())
        return categories[0] if categories else None

    @property
    def primary_category_id(self):
        category = self.primary_category
        return category.id if category else None


class Comment(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="comments")
    name = models.CharField(max_length=200)
    email = models.EmailField()
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ('created',)

    def __str__(self):
        return f"Comment by {self.name} on {self.book}"

