from django.contrib import admin
from .models import Book, Categories

@admin.register(Categories)
class CategoryAdmin(admin.ModelAdmin):

    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    # Columns shown on the main list page
    list_display = ('title', 'author', 'get_categories', 'status', 'created')

    def get_categories(self, obj):
        return ', '.join([category.name for category in obj.categories.all()])
    get_categories.short_description = 'Categories'

    # Clickable links to open the detail view
    list_display_links = ('title',)

    # Right sidebar filters
    list_filter = ('status', 'categories', 'author',)

    # Search bar at top of list page
    search_fields = ('title', 'author', 'description')

    # Live slug auto-fill as you type title
    prepopulated_fields = {'slug': ('title',)}

    # Default list page sorting
    ordering = ('title',)

    # How many items per page in admin
    list_per_page = 20

    # Displays a date navigation bar across the top by year/month/day.
    date_hierarchy = 'created'

    # Replaces large user dropdowns with a search widget when assigning books to user accounts.
    raw_id_fields = ('added_by',)

    readonly_fields = ('created', 'updated')

    list_select_related = ('added_by',)

    fieldsets = (
        ('Book Information', {
            'fields': (
                'title',
                'author',
                'slug',
                'categories',
            )
        }),
        ('Content', {
            'fields': ('description',)
        }),
        ('Publishing', {
            'fields': (
                'status',
                'added_by',
            )
        }),
        ('Dates', {
            'fields': (
                'created',
                'updated',
            )
        }),
    )

    filter_horizontal = ('categories',)




