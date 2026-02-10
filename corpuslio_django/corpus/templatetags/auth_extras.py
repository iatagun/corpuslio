from django import template
from django.contrib.auth.models import Group 
from corpus.permissions import (
    get_user_role_value,
    get_role_display_name,
    user_can_upload_documents,
    user_can_view_advanced_stats,
    user_can_export_data,
    user_can_manage_collections,
    user_can_view_full_document,
    has_role,
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


@register.filter(name='has_role')
def has_role_filter(user, role_name):
    """
    Check if user has at least the specified role.
    Usage: {% if request.user|has_role:"verified" %}
    """
    return has_role(user, role_name)


@register.filter(name='can_upload')
def can_upload_filter(user):
    """
    Check if user has permission to upload documents.
    Usage: {% if request.user|can_upload %}
    """
    return user_can_upload_documents(user)


@register.filter(name='role_display')
def role_display(user):
    """
    Get user's role as display string.
    Usage: {{ request.user|role_display }}
    """
    return get_role_display_name(user)


@register.filter(name='access_level')
def access_level(user):
    """
    Get user's role as display string (alias for role_display).
    Usage: {{ request.user|access_level }}
    """
    return get_role_display_name(user)


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
    return user_can_export_data(user)


@register.filter(name='can_edit_collections')
def can_edit_collections_filter(user):
    """
    Check if user can create/edit collections.
    Usage: {% if request.user|can_edit_collections %}
    """
    return user_can_manage_collections(user)


@register.filter(name='can_view_full_doc')
def can_view_full_doc(user):
    """
    Check if user can view full document content.
    Usage: {% if request.user|can_view_full_doc %}
    """
    return user_can_view_full_document(user)

