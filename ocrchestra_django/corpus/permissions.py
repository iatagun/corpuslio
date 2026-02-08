"""
Permission and access level management for CorpusIO.

This module defines 5-tier role-based access control system aligned with
CORPUS_PLATFORM_VISION.md specifications for national educational corpus platform.

Role Hierarchy:
- ANONYMOUS (0): Guest users, no authentication
- REGISTERED (10): Basic registered users
- VERIFIED (20): Verified researchers (ORCID, institution)
- DEVELOPER (30): API access with authentication
- ADMIN (40): Platform administrators

Each role has specific query limits, export quotas, and feature access.
See UserProfile model for quota enforcement.
"""

from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render


# Role value constants (aligned with UserProfile.ROLE_CHOICES)
ROLE_VALUES = {
    'anonymous': 0,
    'registered': 10,
    'verified': 20,
    'developer': 30,
    'admin': 40,
}


def get_user_role_value(user):
    """
    Get numeric role value for user.
    
    Args:
        user: Django User object (can be AnonymousUser)
        
    Returns:
        int: Role value (0=anonymous, 10=registered, 20=verified, 30=developer, 40=admin)
    """
    if not user or not user.is_authenticated:
        return ROLE_VALUES['anonymous']
    
    # Superusers are always admins (bypass profile)
    if user.is_superuser:
        return ROLE_VALUES['admin']
    
    # Get role from UserProfile (create if missing)
    try:
        profile = user.profile
    except Exception:
        # Profile doesn't exist, create it
        from .models import UserProfile
        initial_role = 'admin' if user.is_superuser else 'registered'
        profile = UserProfile.objects.create(user=user, role=initial_role)
    
    role_map = {
        'registered': ROLE_VALUES['registered'],
        'verified': ROLE_VALUES['verified'],
        'developer': ROLE_VALUES['developer'],
        'admin': ROLE_VALUES['admin'],
    }
    return role_map.get(profile.role, ROLE_VALUES['registered'])


def has_role(user, required_role):
    """
    Check if user meets the required role level.
    
    Args:
        user: Django User object
        required_role: str ('registered', 'verified', 'developer', 'admin')
        
    Returns:
        bool: True if user has required role or higher
    """
    user_value = get_user_role_value(user)
    required_value = ROLE_VALUES.get(required_role, 0)
    return user_value >= required_value


# Decorators for view protection

def role_required(role='registered'):
    """
    Decorator to require minimum role level for a view.
    
    Usage:
        @role_required(role='verified')
        def my_view(request):
            ...
    
    Args:
        role: str - Minimum role required ('registered', 'verified', 'developer', 'admin')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not has_role(request.user, role):
                return render(request, 'corpus/403.html', {
                    'required_role': role,
                    'message': f'Bu sayfaya erişmek için en az {role} rolü gereklidir.'
                }, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def verified_researcher_only(view_func):
    """
    Decorator requiring verified researcher role.
    
    Usage:
        @verified_researcher_only
        def my_view(request):
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not has_role(request.user, 'verified'):
            return render(request, 'corpus/403.html', {
                'required_role': 'verified',
                'message': 'Bu özelliğe erişmek için doğrulanmış araştırmacı olmanız gerekir.'
            }, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


def developer_only(view_func):
    """
    Decorator requiring developer role (API access).
    
    Usage:
        @developer_only
        def my_view(request):
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not has_role(request.user, 'developer'):
            return render(request, 'corpus/403.html', {
                'required_role': 'developer',
                'message': 'Bu özelliğe erişmek için geliştirici hesabı gerekir.'
            }, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_only(view_func):
    """
    Decorator requiring admin role.
    
    Usage:
        @admin_only
        def my_view(request):
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not has_role(request.user, 'admin'):
            return render(request, 'corpus/403.html', {
                'required_role': 'admin',
                'message': 'Bu işlemi sadece yöneticiler gerçekleştirebilir.'
            }, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


# Permission check helpers

def user_can_view_document(user, document):
    """
    Check if user can view a document.
    
    Rules:
    - Anonymous: Only processed=True, public documents
    - Registered: processed=True documents
    - Verified+: All documents
    
    Args:
        user: Django User object
        document: Document model instance
        
    Returns:
        bool: True if user can view document
    """
    role_value = get_user_role_value(user)
    
    # Verified researchers and above can see all documents
    if role_value >= ROLE_VALUES['verified']:
        return True
    
    # Registered users can see processed documents
    if role_value >= ROLE_VALUES['registered']:
        return document.processed
    
    # Anonymous users can only see processed, public documents
    # (public flag to be added to Document model in future)
    return document.processed


def user_can_export_data(user):
    """
    Check if user can export data (CSV, JSON, etc).
    
    Allowed: Registered users and above
    Note: Export quotas still apply (enforced in UserProfile model)
    
    Args:
        user: Django User object
        
    Returns:
        bool: True if user can export
    """
    return has_role(user, 'registered')


def user_can_upload_documents(user):
    """
    Check if user can upload new documents for processing.
    
    Allowed: Verified researchers and above
    
    Args:
        user: Django User object
        
    Returns:
        bool: True if user can upload
    """
    return has_role(user, 'verified')


def user_can_delete_documents(user):
    """
    Check if user can delete documents.
    
    Allowed: Admin only
    
    Args:
        user: Django User object
        
    Returns:
        bool: True if user can delete
    """
    return has_role(user, 'admin')


def user_can_access_api(user):
    """
    Check if user can access the REST API.
    
    Allowed: Developer and above
    
    Args:
        user: Django User object
        
    Returns:
        bool: True if user can access API
    """
    return has_role(user, 'developer')


def user_can_manage_collections(user):
    """
    Check if user can create/edit subcorpus collections.
    
    Allowed: Verified researchers and above
    
    Args:
        user: Django User object
        
    Returns:
        bool: True if user can manage collections
    """
    return has_role(user, 'verified')


def user_can_view_full_document(user):
    """
    Check if user can view full document content.
    
    Allowed: Registered users and above
    (Anonymous users see preview only)
    
    Args:
        user: Django User object
        
    Returns:
        bool: True if user can view full documents
    """
    return has_role(user, 'registered')


def user_can_view_advanced_stats(user):
    """
    Check if user can view advanced statistics (TTR, readability indices, etc).
    
    Allowed: Registered users and above
    
    Args:
        user: Django User object
        
    Returns:
        bool: True if user can view advanced stats
    """
    return has_role(user, 'registered')


def get_document_preview_limit(user):
    """
    Get the document preview character limit for user.
    
    Returns:
        int: Maximum characters to show (None = unlimited)
    """
    if user_can_view_full_document(user):
        return None  # No limit for registered users
    return 2000  # Anonymous users: 2000 chars (~300 words)


def get_concordance_limit(user):
    """
    Get maximum concordance results per query.
    
    Returns:
        int: Maximum number of concordance lines
    """
    role_value = get_user_role_value(user)
    
    if role_value >= ROLE_VALUES['developer']:
        return 10000  # Developers: 10k results
    elif role_value >= ROLE_VALUES['verified']:
        return 1000  # Verified: 1k results
    elif role_value >= ROLE_VALUES['registered']:
        return 500  # Registered: 500 results
    else:
        return 100  # Anonymous: 100 results


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
    
    # Basic stats available to everyone (including anonymous)
    basic_stats = {
        'token_count': stats.get('token_count'),
        'type_count': stats.get('type_count'),
    }
    
    # Advanced stats for registered users and above
    if user_can_view_advanced_stats(user):
        basic_stats.update({
            'ttr': stats.get('ttr'),
            'avg_word_length': stats.get('avg_word_length'),
            'avg_sentence_length': stats.get('avg_sentence_length'),
            'hapax_count': stats.get('hapax_count'),
            'readability_score': stats.get('readability_score'),
        })
    
    return basic_stats


def get_role_display_name(user):
    """
    Get human-readable role name for user.
    
    Args:
        user: Django User object
        
    Returns:
        str: Display name for user's role
    """
    role_value = get_user_role_value(user)
    
    display_names = {
        ROLE_VALUES['anonymous']: 'Misafir',
        ROLE_VALUES['registered']: 'Kayıtlı Kullanıcı',
        ROLE_VALUES['verified']: 'Doğrulanmış Araştırmacı',
        ROLE_VALUES['developer']: 'Geliştirici',
        ROLE_VALUES['admin']: 'Yönetici',
    }
    
    # Find closest match
    for threshold in sorted(ROLE_VALUES.values(), reverse=True):
        if role_value >= threshold:
            return display_names.get(threshold, 'Bilinmeyen')
    
    return 'Misafir'


def get_role_badge_class(user):
    """
    Get CSS badge class for user's role.
    
    Args:
        user: Django User object
        
    Returns:
        str: CSS class name for badge
    """
    role_value = get_user_role_value(user)
    
    if role_value >= ROLE_VALUES['admin']:
        return 'badge-admin'
    elif role_value >= ROLE_VALUES['developer']:
        return 'badge-developer'
    elif role_value >= ROLE_VALUES['verified']:
        return 'badge-verified'
    elif role_value >= ROLE_VALUES['registered']:
        return 'badge-registered'
    else:
        return 'badge-anonymous'

