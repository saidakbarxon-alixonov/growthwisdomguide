# my_books/permissions.py
from rest_framework import permissions


class IsOwnerOrStaffOrReadOnly(permissions.BasePermission):
    """Everyone may READ a book. Only the person who added it
    (or a staff user) may change or delete it.

    Same rule as edit_book_view in views.py.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:   # GET, HEAD, OPTIONS
            return True
        return obj.added_by_id == request.user.id or request.user.is_staff
