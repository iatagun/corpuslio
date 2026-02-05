from django import template
import re

register = template.Library()

@register.filter(name='pos_class')
def pos_class(pos_tag):
    """Convert a POS tag into a safe CSS class suffix.

    Examples:
        'NOUN' -> 'noun'
        'NN' -> 'nn'
        'Adj' -> 'adj'
        'NOUN:Prop' -> 'noun-prop'
    """
    if not pos_tag:
        return 'unknown'
    # Ensure string
    tag = str(pos_tag)
    # Lowercase
    tag = tag.lower()
    # Replace any non-alphanumeric with hyphen
    tag = re.sub(r'[^a-z0-9]+', '-', tag)
    # Trim hyphens
    tag = tag.strip('-')
    return tag or 'unknown'
