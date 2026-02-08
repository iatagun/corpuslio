"""Admin panel configuration for corpus models."""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Sum
from .models import (
    Document, Content, Analysis, ProcessingTask, Tag,
    UserProfile, QueryLog, ExportLog
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin interface for Tag model."""
    
    list_display = ['name', 'color', 'get_document_count', 'created_at']
    list_filter = ['color', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']
    
    def get_document_count(self, obj):
        return obj.get_document_count()
    get_document_count.short_description = 'Belge Sayısı'


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin interface for Document model."""
    
    list_display = ['filename', 'grade_level', 'subject', 'author', 'publisher', 'format', 'upload_date', 'processed']
    list_filter = ['processed', 'format', 'grade_level', 'upload_date', 'tags']
    search_fields = ['filename', 'author', 'subject', 'publisher']
    readonly_fields = ['upload_date']
    filter_horizontal = ['tags']
    
    def get_word_count(self, obj):
        return obj.get_word_count()
    get_word_count.short_description = 'Kelime Sayısı'


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    """Admin interface for Content model."""
    
    list_display = ['document', 'get_text_preview']
    search_fields = ['document__filename', 'cleaned_text']
    
    def get_text_preview(self, obj):
        if obj.cleaned_text:
            return obj.cleaned_text[:100] + '...'
        return '-'
    get_text_preview.short_description = 'Metin Önizleme'


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    """Admin interface for Analysis model."""
    
    list_display = ['document', 'analyzed_at', 'get_word_count']
    list_filter = ['analyzed_at']
    search_fields = ['document__filename']
    readonly_fields = ['analyzed_at']
    
    def get_word_count(self, obj):
        return obj.get_word_count()
    get_word_count.short_description = 'Kelime Sayısı'


@admin.register(ProcessingTask)
class ProcessingTaskAdmin(admin.ModelAdmin):
    """Admin interface for ProcessingTask model."""
    
    list_display = ['document', 'status', 'progress', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at']
    search_fields = ['document__filename', 'task_id']
    readonly_fields = ['task_id', 'created_at', 'updated_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile model."""
    
    list_display = [
        'user', 
        'get_role_badge', 
        'get_verification_status',
        'queries_today', 
        'get_export_usage',
        'created_at'
    ]
    list_filter = ['role', 'verification_status', 'created_at']
    search_fields = ['user__username', 'user__email', 'institution', 'orcid']
    readonly_fields = [
        'created_at', 
        'updated_at', 
        'query_last_reset', 
        'export_last_reset',
        'api_last_reset'
    ]
    
    fieldsets = (
        ('Kullanıcı Bilgileri', {
            'fields': ('user', 'role')
        }),
        ('Doğrulama Bilgileri', {
            'fields': (
                'institution', 
                'orcid', 
                'research_purpose',
                'verification_status',
                'verified_by',
                'verified_at'
            )
        }),
        ('Kotalar ve Kullanım', {
            'fields': (
                'queries_today',
                'query_last_reset',
                'export_quota_mb',
                'export_used_mb',
                'export_last_reset'
            )
        }),
        ('API Erişimi', {
            'fields': (
                'api_key',
                'api_quota_daily',
                'api_calls_today',
                'api_last_reset'
            )
        }),
        ('Diğer', {
            'fields': ('terms_accepted_at', 'created_at', 'updated_at')
        }),
    )
    
    def get_role_badge(self, obj):
        colors = {
            'registered': '#3b82f6',
            'verified': '#10b981',
            'developer': '#f59e0b',
            'admin': '#ef4444',
        }
        color = colors.get(obj.role, '#6b7280')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; border-radius:3px;">{}</span>',
            color,
            obj.get_role_display()
        )
    get_role_badge.short_description = 'Rol'
    
    def get_verification_status(self, obj):
        if obj.verification_status == 'approved':
            return format_html('<span style="color:#10b981;">✓ Onaylandı</span>')
        elif obj.verification_status == 'rejected':
            return format_html('<span style="color:#ef4444;">✗ Reddedildi</span>')
        else:
            return format_html('<span style="color:#f59e0b;">⏳ Beklemede</span>')
    get_verification_status.short_description = 'Doğrulama'
    
    def get_export_usage(self, obj):
        percentage = (obj.export_used_mb / obj.export_quota_mb * 100) if obj.export_quota_mb > 0 else 0
        return f"{obj.export_used_mb:.2f} / {obj.export_quota_mb} MB ({percentage:.0f}%)"
    get_export_usage.short_description = 'Export Kullanımı'


@admin.register(QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    """Admin interface for QueryLog model."""
    
    list_display = [
        'get_user_display',
        'get_query_preview',
        'query_type',
        'result_count',
        'execution_time_ms',
        'rate_limit_hit',
        'created_at'
    ]
    list_filter = [
        'query_type',
        'rate_limit_hit',
        'is_cached',
        'created_at',
        ('user', admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = [
        'query_text',
        'user__username',
        'ip_address'
    ]
    readonly_fields = [
        'user',
        'session_key',
        'ip_address',
        'user_agent',
        'query_text',
        'query_type',
        'document',
        'filters_applied',
        'result_count',
        'execution_time_ms',
        'is_cached',
        'rate_limit_hit',
        'daily_query_count',
        'created_at'
    ]
    date_hierarchy = 'created_at'
    
    def get_user_display(self, obj):
        if obj.user:
            return f"{obj.user.username}"
        return format_html('<span style="color:#6b7280;">Anonymous ({})</span>', obj.ip_address or 'N/A')
    get_user_display.short_description = 'Kullanıcı'
    
    def get_query_preview(self, obj):
        preview = obj.query_text[:50]
        if len(obj.query_text) > 50:
            preview += '...'
        return preview
    get_query_preview.short_description = 'Sorgu'
    
    def has_add_permission(self, request):
        return False  # Logs are auto-created, no manual add
    
    def has_change_permission(self, request, obj=None):
        return False  # Logs are immutable


@admin.register(ExportLog)
class ExportLogAdmin(admin.ModelAdmin):
    """Admin interface for ExportLog model."""
    
    list_display = [
        'user',
        'export_type',
        'format',
        'get_file_size',
        'row_count',
        'download_count',
        'watermark_applied',
        'created_at'
    ]
    list_filter = [
        'export_type',
        'format',
        'watermark_applied',
        'created_at',
        ('user', admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = [
        'user__username',
        'query_text',
        'document__filename'
    ]
    readonly_fields = [
        'user',
        'ip_address',
        'export_type',
        'format',
        'document',
        'query_text',
        'row_count',
        'file_size_bytes',
        'file_size_mb',
        'watermark_applied',
        'citation_text',
        'download_count',
        'last_downloaded_at',
        'file_path',
        'expires_at',
        'quota_before_mb',
        'quota_after_mb',
        'created_at'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Kullanıcı Bilgileri', {
            'fields': ('user', 'ip_address')
        }),
        ('Export Detayları', {
            'fields': (
                'export_type',
                'format',
                'document',
                'query_text',
                'row_count'
            )
        }),
        ('Dosya Bilgileri', {
            'fields': (
                'file_size_bytes',
                'file_size_mb',
                'file_path',
                'expires_at'
            )
        }),
        ('Filigran ve Atıf', {
            'fields': (
                'watermark_applied',
                'citation_text'
            )
        }),
        ('İndirme Takibi', {
            'fields': (
                'download_count',
                'last_downloaded_at'
            )
        }),
        ('Kota Takibi', {
            'fields': (
                'quota_before_mb',
                'quota_after_mb'
            )
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )
    
    def get_file_size(self, obj):
        if obj.file_size_mb >= 1:
            return f"{obj.file_size_mb:.2f} MB"
        else:
            return f"{obj.file_size_bytes:,} bytes"
    get_file_size.short_description = 'Dosya Boyutu'
    
    def has_add_permission(self, request):
        return False  # Logs are auto-created, no manual add
    
    def has_change_permission(self, request, obj=None):
        return False  # Logs are immutable


from .collections import Collection, QueryHistory

admin.site.register(Collection)
admin.site.register(QueryHistory)
