"""Admin interface for API models."""

from django.contrib import admin
from .models import APIKey


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    """Admin interface for API keys."""
    
    list_display = ['name', 'user', 'tier', 'is_active', 'requests_today', 'total_requests', 'created_at', 'expires_at']
    list_filter = ['tier', 'is_active', 'created_at']
    search_fields = ['name', 'user__username', 'user__email', 'key']
    readonly_fields = ['key', 'requests_today', 'total_requests', 'last_request', 'created_at']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['user', 'name', 'key']
        }),
        ('Tier & Permissions', {
            'fields': ['tier', 'is_active', 'expires_at']
        }),
        ('Usage Statistics', {
            'fields': ['requests_today', 'total_requests', 'last_request']
        }),
        ('Security', {
            'fields': ['allowed_ips'],
            'classes': ['collapse']
        }),
    ]
    
    def get_readonly_fields(self, request, obj=None):
        """Make key readonly only after creation."""
        if obj:  # Editing existing object
            return self.readonly_fields
        return ['requests_today', 'total_requests', 'last_request', 'created_at']
    
    actions = ['reset_daily_quota', 'deactivate_keys']
    
    def reset_daily_quota(self, request, queryset):
        """Reset daily quota for selected API keys."""
        count = queryset.update(requests_today=0)
        self.message_user(request, f'Reset daily quota for {count} API keys.')
    reset_daily_quota.short_description = 'Reset daily quota'
    
    def deactivate_keys(self, request, queryset):
        """Deactivate selected API keys."""
        count = queryset.update(is_active=False)
        self.message_user(request, f'Deactivated {count} API keys.')
    deactivate_keys.short_description = 'Deactivate selected keys'

