"""
Permission and access level management for CorpusIO.

This module defines access levels and permission checks for the tiered access system.
"""

from enum import IntEnum


class AccessLevel(IntEnum):
    """
    User access levels in ascending order of permissions.
    Higher values have more access.
    """
    ANONYMOUS = 0      # Not logged in
    STUDENT = 1        # Student group member
    ACADEMICIAN = 2    # Academician group member
    DEVELOPER = 3      # Developer group member  
    SUPERUSER = 4      # Django superuser


def get_user_access_level(user):
    """
    Determine the access level of a user.
    
    Args:
        user: Django User object (can be AnonymousUser)
        
    Returns:
        AccessLevel: The user's access level
    """
    if not user or not user.is_authenticated:
        return AccessLevel.ANONYMOUS
    
    if user.is_superuser:
        return AccessLevel.SUPERUSER
    
    # Check group membership
    user_groups = set(user.groups.values_list('name', flat=True))
    
    if 'Developer' in user_groups:
        return AccessLevel.DEVELOPER
    elif 'Academician' in user_groups:
        return AccessLevel.ACADEMICIAN
    elif 'Student' in user_groups:
        return AccessLevel.STUDENT
    
    # Default for authenticated users without specific groups
    return AccessLevel.STUDENT


def has_access_level(user, required_level):
    """
    Check if user meets the required access level.
    
    Args:
        user: Django User object
        required_level: AccessLevel or int
        
    Returns:
        bool: True if user has required level or higher
    """
    user_level = get_user_access_level(user)
    return user_level >= required_level


# Permission check helpers

def user_can_view_advanced_stats(user):
    """
    Check if user can view advanced statistics (TTR, readability, etc).
    
    Allowed: Student and above
    """
    return has_access_level(user, AccessLevel.STUDENT)


def user_can_upload(user):
    """
    Check if user can upload documents.
    
    Allowed: Academician and above
    """
    return has_access_level(user, AccessLevel.ACADEMICIAN)


def user_can_export(user):
    """
    Check if user can export data (CSV, JSON, etc).
    
    Allowed: Student and above
    """
    return has_access_level(user, AccessLevel.STUDENT)


def user_can_edit_collections(user):
    """
    Check if user can create/edit collections.
    
    Allowed: Academician and above
    """
    return has_access_level(user, AccessLevel.ACADEMICIAN)


def user_can_delete_documents(user):
    """
    Check if user can delete documents.
    
    Allowed: Developer and above (or own documents for Academician)
    """
    return has_access_level(user, AccessLevel.DEVELOPER)


def user_can_access_api(user):
    """
    Check if user can access the API.
    
    Allowed: Academician and above
    """
    return has_access_level(user, AccessLevel.ACADEMICIAN)


def user_can_view_full_document(user):
    """
    Check if user can view full document content.
    
    Allowed: Student and above (Anonymous users see preview only)
    """
    return has_access_level(user, AccessLevel.STUDENT)


def get_document_preview_limit(user):
    """
    Get the document preview word limit for user.
    
    Returns:
        int: Maximum words to show (None = unlimited)
    """
    if user_can_view_full_document(user):
        return None  # No limit
    return 500  # Anonymous users: 500 words


def filter_stats_by_access_level(stats, user):
    """
    Filter statistics dictionary based on user access level.
    
    Args:
        stats: Dictionary of statistics
        user: Django User object
        
    Returns:
        dict: Filtered statistics appropriate for user's access level
    """
    if not stats:
        return {}
    
    # Basic stats available to everyone
    basic_stats = {
        'token_count': stats.get('token_count'),
        'type_count': stats.get('type_count'),
    }
    
    # Advanced stats for Student and above
    if user_can_view_advanced_stats(user):
        basic_stats.update({
            'ttr': stats.get('ttr'),
            'avg_word_length': stats.get('avg_word_length'),
            'avg_sentence_length': stats.get('avg_sentence_length'),
        })
    
    return basic_stats


def get_access_level_display(user):
    """
    Get human-readable access level name.
    
    Returns:
        str: Display name for user's access level
    """
    level = get_user_access_level(user)
    
    display_names = {
        AccessLevel.ANONYMOUS: 'Ziyaretçi',
        AccessLevel.STUDENT: 'Öğrenci',
        AccessLevel.ACADEMICIAN: 'Akademisyen',
        AccessLevel.DEVELOPER: 'Geliştirici',
        AccessLevel.SUPERUSER: 'Süper Kullanıcı',
    }
    
    return display_names.get(level, 'Bilinmeyen')
