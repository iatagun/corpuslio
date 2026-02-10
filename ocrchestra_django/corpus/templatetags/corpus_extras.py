from django import template
import os

register = template.Library()

@register.filter
def basename(value):
    """Returns the basename of a file path."""
    if not value:
        return ''
    return os.path.basename(str(value))
