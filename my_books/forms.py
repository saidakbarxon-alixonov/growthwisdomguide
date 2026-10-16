from django import forms
from .models import Book, Categories, Comment
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

MAX_NEW_CATEGORIES = 5   # how many new categories can be typed in one go


class BookForm(forms.ModelForm):

    # Several brand-new categories can be typed at once, separated by commas.
    new_categories = forms.CharField(
        required=False,
        max_length=300,
        label="New categories",
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. Health, Relationships, Business',
        })
    )

    class Meta:
        model = Book
        fields = ['title', 'author', 'categories', 'description', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g. Atomic Habits'}),
            'author': forms.TextInput(attrs={'placeholder': 'e.g. James Clear'}),
            # Tick boxes instead of a multi-select list: click as many as you like.
            'categories': forms.CheckboxSelectMultiple,
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'What is the main idea, and why is it worth reading?',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categories'].queryset = Categories.objects.order_by('name')

    def clean_title(self):
        title = self.cleaned_data['title'].strip()

        if len(title) < 3:
            raise forms.ValidationError("Title is too short. Use at least 3 characters.")

        return title

    def clean_new_categories(self):
        """Turn "Health,  business, health" into ['Health', 'business']."""
        raw = self.cleaned_data.get('new_categories', '')
        names, seen = [], set()

        for part in raw.split(','):
            name = ' '.join(part.split())          # trim and collapse spaces
            if not name or name.lower() in seen:   # skip empties and duplicates
                continue
            if len(name) > 100:
                raise forms.ValidationError("Each category name must be 100 characters or fewer.")
            seen.add(name.lower())
            names.append(name)

        if len(names) > MAX_NEW_CATEGORIES:
            raise forms.ValidationError(
                f"Add at most {MAX_NEW_CATEGORIES} new categories at a time.")

        return names

    def get_new_categories(self):
        """Create the typed categories (or reuse ones that already exist).

        "habits" and "Habits" count as the same category, so we never end up
        with two almost-identical ones.
        """
        categories = []
        for name in self.cleaned_data.get('new_categories', []):
            category = Categories.objects.filter(name__iexact=name).first()
            if category is None:
                category = Categories.objects.create(name=name)
            categories.append(category)
        return categories


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Enter your username',
            'autocomplete': 'username',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
        })
    )


class CustomRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'auth-input'
        self.fields['username'].widget.attrs['placeholder'] = 'Choose a username'
        self.fields['email'].widget.attrs['placeholder'] = 'name@example.com'

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('name', 'email', 'body')

class EmailPostForm(forms.Form):
    """The "email this book to a friend" form."""

    name = forms.CharField(max_length=60, label="Your name")
    email = forms.EmailField(label="Your email")
    to = forms.EmailField(label="Friend's email")
    comments = forms.CharField(
        required=False,
        max_length=500,
        label="Message (optional)",
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Why do you think they will enjoy it?',
        }),
    )

    def clean_name(self):
        # One line only: the name ends up in the email subject.
        return ' '.join(self.cleaned_data['name'].split())
