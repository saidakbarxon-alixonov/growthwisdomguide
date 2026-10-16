from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from .forms import BookForm
from .models import Book, Categories


class BookModelTest(TestCase):

    def test_slug_is_created_from_title(self):
        book = Book.objects.create(title='The Power of Habit', author='Charles Duhigg')
        self.assertEqual(book.slug, 'the-power-of-habit')

    def test_same_title_gets_a_different_slug(self):
        Book.objects.create(title='Grit', author='A')
        second = Book.objects.create(title='Grit', author='B')
        self.assertEqual(second.slug, 'grit-1')

    def test_book_can_have_many_categories(self):
        book = Book.objects.create(title='Atomic Habits', author='James Clear')
        habits = Categories.objects.create(name='Habits')
        focus = Categories.objects.create(name='Focus')
        book.categories.add(habits, focus)
        self.assertEqual(book.categories.count(), 2)
        self.assertEqual(habits.books.count(), 1)


class PageTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('sam', 'sam@example.com', 'secret12345')
        self.habits = Categories.objects.create(name='Habits')
        self.focus = Categories.objects.create(name='Focus')
        self.atomic = Book.objects.create(
            title='Atomic Habits', author='James Clear', added_by=self.user)
        self.atomic.categories.add(self.habits, self.focus)
        self.deep = Book.objects.create(title='Deep Work', author='Cal Newport')
        self.deep.categories.add(self.focus)
        self.loose = Book.objects.create(title='Free Book', author='Nobody')  # no category
        self.draft = Book.objects.create(
            title='Secret Draft', author='Me', status='draft')
        self.draft.categories.add(self.habits)

    def test_home_page_shows_a_shelf_per_category(self):
        response = self.client.get(reverse('my_books:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Habits')
        self.assertContains(response, 'More to explore')    # the uncategorised book
        self.assertContains(response, 'Free Book')
        self.assertNotContains(response, 'Secret Draft')    # drafts stay hidden

    def test_book_in_two_categories_appears_on_both_category_pages(self):
        for category in (self.habits, self.focus):
            response = self.client.get(category.get_absolute_url())
            self.assertContains(response, 'Atomic Habits')

    def test_category_page_only_lists_its_own_published_books(self):
        response = self.client.get(self.habits.get_absolute_url())
        self.assertContains(response, 'Atomic Habits')
        self.assertNotContains(response, 'Deep Work')
        self.assertNotContains(response, 'Secret Draft')

    def test_unknown_category_is_404(self):
        response = self.client.get(reverse('my_books:category_detail', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_book_detail_and_search(self):
        response = self.client.get(self.atomic.get_absolute_url())
        self.assertContains(response, 'Atomic Habits')
        response = self.client.get(reverse('my_books:book_list'), {'q': 'newport'})
        self.assertContains(response, 'Deep Work')
        self.assertNotContains(response, 'Atomic Habits')

    def test_sidebar_marks_the_current_category(self):
        response = self.client.get(self.focus.get_absolute_url())
        self.assertContains(response, 'aria-current="page"', count=1)


class AddAndEditBookTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('sam', 'sam@example.com', 'secret12345')
        self.other = User.objects.create_user('lee', 'lee@example.com', 'secret12345')
        self.habits = Categories.objects.create(name='Habits')

    def test_add_book_requires_login(self):
        response = self.client.get(reverse('my_books:add_book'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    def test_add_book_with_ticked_and_new_categories(self):
        self.client.login(username='sam', password='secret12345')
        response = self.client.post(reverse('my_books:add_book'), {
            'title': 'Mindset', 'author': 'Carol Dweck', 'description': '',
            'categories': [self.habits.pk],
            'new_categories': 'Psychology,  Growth , psychology',
            'status': 'published',
        })
        book = Book.objects.get(title='Mindset')
        self.assertRedirects(response, book.get_absolute_url())
        self.assertEqual(book.added_by, self.user)
        self.assertEqual(
            sorted(book.categories.values_list('name', flat=True)),
            ['Growth', 'Habits', 'Psychology'])       # duplicate "psychology" ignored

    def test_new_category_matches_existing_one_ignoring_case(self):
        self.client.login(username='sam', password='secret12345')
        self.client.post(reverse('my_books:add_book'), {
            'title': 'Tiny Habits', 'author': 'BJ Fogg', 'new_categories': 'habits',
            'status': 'published',
        })
        self.assertEqual(Categories.objects.filter(name__iexact='habits').count(), 1)
        self.assertEqual(Book.objects.get(title='Tiny Habits').categories.get(), self.habits)

    def test_too_many_new_categories_is_rejected(self):
        form = BookForm({
            'title': 'Big Book', 'author': 'X', 'status': 'published',
            'new_categories': 'a,b,c,d,e,f',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('new_categories', form.errors)

    def test_short_title_is_rejected(self):
        form = BookForm({'title': 'ab', 'author': 'X', 'status': 'published'})
        self.assertFalse(form.is_valid())

    def test_category_query_string_prefills_the_form(self):
        self.client.login(username='sam', password='secret12345')
        response = self.client.get(reverse('my_books:add_book'), {'category': self.habits.pk})
        self.assertContains(response, 'checked')

    def test_owner_can_edit_categories_but_others_cannot(self):
        book = Book.objects.create(title='Grit', author='A. Duckworth', added_by=self.user)
        url = reverse('my_books:edit_book', args=[book.slug])
        payload = {'title': 'Grit', 'author': 'A. Duckworth', 'status': 'published',
                   'categories': [self.habits.pk], 'new_categories': 'Mindset'}

        self.client.login(username='lee', password='secret12345')
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, payload).status_code, 403)

        self.client.login(username='sam', password='secret12345')
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.post(url, payload)
        self.assertEqual(
            sorted(book.categories.values_list('name', flat=True)), ['Habits', 'Mindset'])


class ShareBookTests(TestCase):

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user('sam', 'sam@example.com', 'secret12345')
        self.book = Book.objects.create(
            title='Deep Work', author='Cal Newport', description='Focus without distraction.')
        self.url = reverse('my_books:share_book', args=[self.book.slug])
        self.payload = {'name': 'Sam', 'email': 'sam@example.com',
                        'to': 'friend@example.com', 'comments': 'Read chapter 2!'}

    def test_share_menu_is_on_the_book_page(self):
        response = self.client.get(self.book.get_absolute_url())
        self.assertContains(response, 'class="share"')
        self.assertContains(response, 'Email a friend')
        self.assertContains(response, 'https://t.me/share/url')

    def test_email_form_needs_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_email_is_sent(self):
        self.client.login(username='sam', password='secret12345')
        response = self.client.post(self.url, self.payload)
        self.assertRedirects(response, self.book.get_absolute_url())
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ['friend@example.com'])
        self.assertEqual(message.reply_to, ['sam@example.com'])
        self.assertIn('Deep Work', message.subject)
        self.assertIn('Read chapter 2!', message.body)
        self.assertIn(self.book.get_absolute_url(), message.body)

    def test_invalid_address_sends_nothing(self):
        self.client.login(username='sam', password='secret12345')
        response = self.client.post(self.url, {**self.payload, 'to': 'not-an-email'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_sharing_is_limited_per_hour(self):
        self.client.login(username='sam', password='secret12345')
        for _ in range(5):
            self.client.post(self.url, self.payload)
        response = self.client.post(self.url, self.payload)
        self.assertEqual(len(mail.outbox), 5)
        self.assertContains(response, 'try again a little later')

    def test_draft_books_cannot_be_shared(self):
        draft = Book.objects.create(title='Draft', author='Me', status='draft')
        self.client.login(username='sam', password='secret12345')
        response = self.client.get(reverse('my_books:share_book', args=[draft.slug]))
        self.assertEqual(response.status_code, 404)
