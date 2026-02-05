from django import template
from django.contrib.auth.models import Group 
from corpus.permissions import (
    get_user_access_level,
    get_access_level_display,
    user_can_upload,
    user_can_view_advanced_stats,
    user_can_export,
    user_can_edit_collections,
    user_can_view_full_document,
)

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
def can_upload_filter(user):
    """
    Check if user has permission to upload documents.
    Usage: {% if request.user|can_upload %}
    """
    return user_can_upload(user)


@register.filter(name='access_level')
def access_level(user):
    """
    Get user's access level as display string.
    Usage: {{ request.user|access_level }}
    """
    return get_access_level_display(user)


@register.filter(name='can_see_advanced_stats')
def can_see_advanced_stats(user):
    """
    Check if user can see advanced statistics (TTR, readability).
    Usage: {% if request.user|can_see_advanced_stats %}
    """
    return user_can_view_advanced_stats(user)


@register.filter(name='can_export')
def can_export_filter(user):
    """
    Check if user can export data.
    Usage: {% if request.user|can_export %}
    """
    return user_can_export(user)


@register.filter(name='can_edit_collections')
def can_edit_collections_filter(user):
    """
    Check if user can create/edit collections.
    Usage: {% if request.user|can_edit_collections %}
    """
    return user_can_edit_collections(user)


@register.filter(name='can_view_full_doc')
def can_view_full_doc(user):
    """
    Check if user can view full document content.
    Usage: {% if request.user|can_view_full_doc %}
    """
    return user_can_view_full_document(user)
