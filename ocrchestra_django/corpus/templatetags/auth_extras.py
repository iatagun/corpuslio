from django import template
from django.contrib.auth.models import Group 

register = template.Library() 

@register.filter(name='has_group') 
def has_group(user, group_name):
    """
    Check if user belongs to a specific group.
    Usage: {% if request.user|has_group:"GroupName" %}
    """
    if not user.is_authenticated:
        return False
    return user.groups.filter(name=group_name).exists()


@register.filter(name='can_upload')
def can_upload(user):
    """
    Check if user has permission to upload documents.
    Usage: {% if request.user|can_upload %}
    """
    if not user.is_authenticated:
        return False
    return (
        user.groups.filter(name__in=['Academician', 'Developer']).exists() 
        or user.is_superuser
    )
