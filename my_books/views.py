# my_books/views.py
import smtplib

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMessage
from django.db.models import Count, Prefetch, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView

from my_books.models import Book, Categories
from .forms import (
    BookForm, CommentForm, CustomLoginForm, CustomRegistrationForm, EmailPostForm,
)

BOOKS_PER_SHELF = 3        # books shown per category on the home page (one row)
BOOKS_PER_PAGE = 9         # three rows of three
SHARE_LIMIT = 5            # emails one user may send ...
SHARE_WINDOW = 60 * 60     # ... per hour (protects the site from being used for spam)


def with_categories(books):
    """Load each book's categories together with the books (2 queries in total
    instead of 1 extra query per book). Categories come sorted by name."""
    return books.prefetch_related(
        Prefetch('categories', queryset=Categories.objects.order_by('name'))
    )


class BookListView(ListView):
    template_name = 'books/book_list.html'
    context_object_name = 'books'
    paginate_by = BOOKS_PER_PAGE

    def get_queryset(self):
        books = with_categories(Book.published).order_by('-created')

        # Search box in the top bar sends ?q=...
        query = self.request.GET.get('q', '').strip()
        if query:
            books = books.filter(
                Q(title__icontains=query)
                | Q(author__icontains=query)
                | Q(description__icontains=query)
            )
        return books

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '').strip()
        return context


class CategoryDetailView(ListView):
    """One page per category: /category/<id>/ lists only that category's books."""
    template_name = 'books/category_detail.html'
    context_object_name = 'books'
    paginate_by = BOOKS_PER_PAGE

    def get_queryset(self):
        self.category = get_object_or_404(Categories, pk=self.kwargs['pk'])
        return (
            with_categories(Book.published.filter(categories=self.category))
            .order_by('-created')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


def home_page(request):
    """Overview: a short shelf (one row) for every category that has books."""
    categories = (
        Categories.objects
        .annotate(book_count=Count('books', filter=Q(books__status='published')))
        .filter(book_count__gt=0)
        .order_by('name')
    )
    shelves = {c.pk: {'category': c, 'books': []} for c in categories}
    uncategorised = []

    # One pass over the books (newest first) fills every shelf.
    for book in with_categories(Book.published).order_by('-created'):
        book_categories = list(book.categories.all())
        if not book_categories:
            uncategorised.append(book)
        for category in book_categories:
            shelf = shelves.get(category.pk)
            if shelf and len(shelf['books']) < BOOKS_PER_SHELF:
                shelf['books'].append(book)

    return render(request, 'home/index.html', {
        'shelves': list(shelves.values()),
        'uncategorised': uncategorised[:BOOKS_PER_SHELF],
        'uncategorised_count': len(uncategorised),
        'has_books': bool(shelves or uncategorised),
    })


def save_book_form(form, user):
    """Save a BookForm: the book, the ticked categories and any new typed ones."""
    book = form.save(commit=False)
    if book.added_by_id is None:
        book.added_by = user
    book.save()
    form.save_m2m()                                   # the ticked categories
    for category in form.get_new_categories():        # the typed ones
        book.categories.add(category)
    return book


@login_required
def add_book_view(request):
    if request.method == "POST":
        form = BookForm(request.POST)
        if form.is_valid():
            book = save_book_form(form, request.user)
            return redirect(book.get_absolute_url())
    else:
        # /books/add/?category=3 opens the form with category 3 already ticked
        # (used by the "Add a book" button on a category page).
        initial = {}
        category_id = request.GET.get('category', '')
        if category_id.isdigit():
            initial['categories'] = [int(category_id)]
        form = BookForm(initial=initial)

    return render(request, 'books/add_book.html', {'form': form, 'editing': False})


@login_required
def edit_book_view(request, slug):
    """Change a book's details and categories from the browser (no admin needed)."""
    book = get_object_or_404(Book, slug=slug)
    if book.added_by_id != request.user.id and not request.user.is_staff:
        raise PermissionDenied

    if request.method == "POST":
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            save_book_form(form, request.user)
            messages.success(request, "Your changes are saved.")
            return redirect(book.get_absolute_url())
    else:
        form = BookForm(instance=book)

    return render(request, 'books/add_book.html', {
        'form': form, 'editing': True, 'book': book,
    })


def book_detail_view(request, slug):
    book = get_object_or_404(
        with_categories(Book.objects.select_related('added_by')),
        slug=slug
    )

    comments = book.comments.filter(active=True)
    new_comment = None

    if request.method == 'POST':
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.book = book
            new_comment.save()
    else:
        comment_form = CommentForm()

    can_edit = request.user.is_authenticated and (
        book.added_by_id == request.user.id or request.user.is_staff
    )

    return render(request, 'books/book_detail.html', {
        'book': book,
        'comments': comments,
        'new_comment': new_comment,
        'comment_form': comment_form,
        'can_edit': can_edit,
        # Full address (http://...) for the Share menu; relative links don't work in a chat.
        'share_url': request.build_absolute_uri(book.get_absolute_url()),
        'share_text': f"{book.title} by {book.author}",
    })


@login_required
def share_book_view(request, slug):
    """Email a book recommendation to a friend."""
    book = get_object_or_404(with_categories(Book.published), slug=slug)
    book_url = request.build_absolute_uri(book.get_absolute_url())

    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            throttle_key = f"share-count-{request.user.pk}"
            cache.add(throttle_key, 0, SHARE_WINDOW)

            if cache.get(throttle_key, 0) >= SHARE_LIMIT:
                form.add_error(None, "You have shared a lot of books in the last hour. "
                                     "Please try again a little later.")
            else:
                email = EmailMessage(
                    subject=f"{data['name']} recommends: {book.title}",
                    body=build_share_email(data, book, book_url),
                    to=[data['to']],
                    reply_to=[data['email']],   # replies go to the person who shared
                )
                try:
                    email.send()
                except (OSError, smtplib.SMTPException):
                    form.add_error(None, "We could not send the email right now. "
                                         "Please try again later.")
                else:
                    cache.incr(throttle_key)
                    messages.success(request, f"“{book.title}” was sent to {data['to']}.")
                    return redirect(book.get_absolute_url())
    else:
        form = EmailPostForm(initial={
            'name': request.user.get_full_name() or request.user.username,
            'email': request.user.email,
        })

    return render(request, 'books/share_book.html', {
        'form': form, 'book': book, 'book_url': book_url,
    })


def build_share_email(data, book, book_url):
    """The plain-text body of the recommendation email."""
    lines = [
        "Hi!",
        "",
        f"{data['name']} thinks you will enjoy this book:",
        "",
        f"{book.title}, by {book.author}",
    ]
    if book.description:
        summary = book.description.strip()
        if len(summary) > 300:
            summary = summary[:300].rsplit(' ', 1)[0] + "..."
        lines += ["", summary]
    lines += ["", f"Read more: {book_url}"]
    if data['comments']:
        lines += ["", f"A message from {data['name']}:", data['comments']]
    lines += ["", "-- Sent from GrowthWisdomGuide"]
    return "\n".join(lines)


class CustomLoginView(LoginView):
    form_class = CustomLoginForm
    template_name = 'registration/login.html'


def register_view(request):
    if request.user.is_authenticated:
        return redirect('my_books:index')

    if request.method == 'POST':
        form = CustomRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('my_books:index')
    else:
        form = CustomRegistrationForm()

    return render(request, 'registration/register.html', {'form': form})
