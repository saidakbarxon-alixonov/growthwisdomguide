# my_books/serializers.py
#
# A serializer is the "translator" of an API:
#     Book object (Python)  <-->  JSON (text that travels over the internet)
#
# It also checks incoming JSON, the same way your BookForm checks a form.
from rest_framework import serializers

from .models import Book, Categories


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = ['id', 'name']


class BookSerializer(serializers.ModelSerializer):
    # What the client SENDS: a list of category ids, e.g. "categories": [1, 3]
    categories = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Categories.objects.all(),
        required=False,
    )
    # What the client GETS BACK as a bonus: the names, e.g. ["Habits", "Health"]
    # (read_only = it is only for output, the client cannot send it)
    category_names = serializers.StringRelatedField(
        source='categories', many=True, read_only=True,
    )
    # Show the username of whoever added the book instead of a bare id.
    # (default=None -> a book added in the admin shows "added_by": null)
    added_by = serializers.CharField(
        source='added_by.username', read_only=True, default=None)

    class Meta:
        model = Book
        fields = [
            'id', 'slug', 'title', 'author', 'description',
            'categories', 'category_names',
            'added_by', 'status', 'created', 'updated',
        ]
        # The server decides these, the client may not change them.
        read_only_fields = ['id', 'slug', 'status', 'created', 'updated']

    # Same rule as clean_title() in your BookForm.
    def validate_title(self, value):
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError(
                "Title is too short. Use at least 3 characters.")
        return value
