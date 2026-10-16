from django import template

register = template.Library()

# How many accent colours the CSS defines (.hue-0 ... .hue-4).
HUE_COUNT = 5


@register.filter
def hue(value):
    """Turn an id (e.g. a category id) into a number 0-4.

    Used as a CSS class, so every category keeps the same accent colour
    on the sidebar, the book cards and the book page.
    Usage: class="hue-{{ book.category_id|hue }}"
    """
    try:
        return int(value) % HUE_COUNT
    except (TypeError, ValueError):
        return 0
