"""Admin panel configuration for corpus models."""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Sum
from .models import (
    Document, Content, Analysis, ProcessingTask, Tag,
    UserProfile, QueryLog, ExportLog,
    DataExportRequest, ConsentRecord, AccountDeletionRequest,  # Week 11: GDPR
    Sentence, Token, CorpusMetadata  # Corpus Query Models
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


# ============================================================
# KVKK/GDPR COMPLIANCE ADMIN (Week 11)
# ============================================================

@admin.register(DataExportRequest)
class DataExportRequestAdmin(admin.ModelAdmin):
    """Admin interface for Data Export Requests (KVKK/GDPR)."""
    
    list_display = [
        'id', 'user', 'format', 'get_status_badge', 
        'requested_at', 'completed_at', 'download_count', 'is_expired_status'
    ]
    list_filter = ['status', 'format', 'requested_at', 'completed_at']
    search_fields = ['user__username', 'user__email', 'ip_address']
    readonly_fields = [
        'requested_at', 'processed_at', 'completed_at', 'downloaded_at',
        'ip_address', 'user_agent', 'error_message'
    ]
    date_hierarchy = 'requested_at'
    
    fieldsets = (
        ('Kullanıcı Bilgisi', {
            'fields': ('user', 'format')
        }),
        ('Durum', {
            'fields': ('status', 'error_message')
        }),
        ('Tarihler', {
            'fields': (
                'requested_at',
                'processed_at',
                'completed_at',
                'expires_at'
            )
        }),
        ('Dosyalar', {
            'fields': ('json_file', 'csv_file')
        }),
        ('İndirme Takibi', {
            'fields': ('downloaded_at', 'download_count')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def get_status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            'pending': 'gray',
            'processing': 'blue',
            'completed': 'green',
            'failed': 'red',
            'expired': 'orange',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    get_status_badge.short_description = 'Durum'
    
    def is_expired_status(self, obj):
        """Check if export is expired."""
        if obj.is_expired():
            return format_html('<span style="color: red;">✗ Süresi Doldu</span>')
        elif obj.status == 'completed':
            return format_html('<span style="color: green;">✓ Geçerli</span>')
        return '-'
    is_expired_status.short_description = 'Geçerlilik'
    
    def has_add_permission(self, request):
        return False  # Requests created by users only


@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    """Admin interface for Consent Records (KVKK/GDPR)."""
    
    list_display = [
        'id', 'user', 'consent_type', 'get_consent_badge',
        'consented_at', 'withdrawn_at', 'policy_version'
    ]
    list_filter = ['consent_type', 'consented', 'policy_version', 'consented_at']
    search_fields = ['user__username', 'user__email', 'ip_address']
    readonly_fields = [
        'consented_at', 'withdrawn_at',
        'ip_address', 'user_agent'
    ]
    date_hierarchy = 'consented_at'
    
    fieldsets = (
        ('İzin Bilgisi', {
            'fields': ('user', 'consent_type', 'consented', 'policy_version')
        }),
        ('Tarihler', {
            'fields': ('consented_at', 'withdrawn_at')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def get_consent_badge(self, obj):
        """Display consent status as badge."""
        if obj.consented and not obj.withdrawn_at:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-weight: bold;">✓ İzin Verildi</span>'
            )
        else:
            return format_html(
                '<span style="background-color: red; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-weight: bold;">✗ İzin Yok</span>'
            )
    get_consent_badge.short_description = 'Durum'
    
    def has_add_permission(self, request):
        return False  # Consents managed by users only


@admin.register(AccountDeletionRequest)
class AccountDeletionRequestAdmin(admin.ModelAdmin):
    """Admin interface for Account Deletion Requests (KVKK/GDPR)."""
    
    list_display = [
        'id', 'user', 'deletion_type', 'get_status_badge',
        'requested_at', 'grace_period_ends_at', 'completed_at'
    ]
    list_filter = ['status', 'deletion_type', 'requested_at']
    search_fields = ['user__username', 'user__email', 'reason', 'ip_address']
    readonly_fields = [
        'requested_at', 'grace_period_ends_at',
        'processed_at', 'completed_at', 'cancelled_at',
        'documents_count', 'queries_count', 'exports_count',
        'ip_address'
    ]
    date_hierarchy = 'requested_at'
    
    fieldsets = (
        ('Kullanıcı Bilgisi', {
            'fields': ('user', 'deletion_type', 'reason')
        }),
        ('Durum', {
            'fields': ('status',)
        }),
        ('Tarihler', {
            'fields': (
                'requested_at',
                'grace_period_ends_at',
                'processed_at',
                'completed_at',
                'cancelled_at'
            )
        }),
        ('Veri Özeti', {
            'fields': (
                'documents_count',
                'queries_count',
                'exports_count'
            )
        }),
        ('Metadata', {
            'fields': ('ip_address',),
            'classes': ('collapse',)
        }),
    )
    
    def get_status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            'pending': 'gray',
            'grace_period': 'orange',
            'processing': 'blue',
            'completed': 'red',
            'cancelled': 'green',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    get_status_badge.short_description = 'Durum'
    
    def has_add_permission(self, request):
        return False  # Requests created by users only
    
    def has_change_permission(self, request, obj=None):
        # Allow viewing but not changing
        return True
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of deletion requests (audit trail)
        return False


# ============================================================================
# CORPUS QUERY ADMIN INTERFACES
# ============================================================================

class TokenInline(admin.TabularInline):
    """Inline display of tokens within a sentence."""
    model = Token
    extra = 0
    fields = ['index', 'form', 'lemma', 'upos', 'deprel']
    readonly_fields = ['index', 'form', 'lemma', 'upos', 'deprel']
    can_delete = False
    max_num = 20  # Show first 20 tokens
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Sentence)
class SentenceAdmin(admin.ModelAdmin):
    """Admin interface for Sentence model."""
    
    list_display = ['id', 'document', 'index', 'text_preview', 'token_count']
    list_filter = ['document']
    search_fields = ['text', 'document__filename']
    readonly_fields = ['index', 'text', 'token_count', 'metadata']
    inlines = [TokenInline]
    
    def text_preview(self, obj):
        preview = obj.text[:80] + '...' if len(obj.text) > 80 else obj.text
        return preview
    text_preview.short_description = 'Cümle'
    
    def has_add_permission(self, request):
        return False  # Sentences created via import only
    
    def has_change_permission(self, request, obj=None):
        return True  # View only
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    """Admin interface for Token model."""
    
    list_display = ['id', 'form', 'lemma', 'upos', 'sentence_preview', 'document']
    list_filter = ['upos', 'document']
    search_fields = ['form', 'lemma']
    readonly_fields = [
        'document', 'sentence', 'index', 'form', 'lemma', 
        'upos', 'xpos', 'feats', 'head', 'deprel', 'deps', 'misc',
        'vrt_attributes'
    ]
    
    fieldsets = (
        ('Token Info', {
            'fields': ('document', 'sentence', 'index', 'form')
        }),
        ('Linguistic Annotations', {
            'fields': ('lemma', 'upos', 'xpos', 'feats')
        }),
        ('Dependency Parsing', {
            'fields': ('head', 'deprel', 'deps')
        }),
        ('Additional', {
            'fields': ('misc', 'vrt_attributes'),
            'classes': ('collapse',)
        }),
    )
    
    def sentence_preview(self, obj):
        preview = obj.sentence.text[:50] + '...' if len(obj.sentence.text) > 50 else obj.sentence.text
        return preview
    sentence_preview.short_description = 'Cümle'
    
    def has_add_permission(self, request):
        return False  # Tokens created via import only
    
    def has_change_permission(self, request, obj=None):
        return True  # View only
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(CorpusMetadata)
class CorpusMetadataAdmin(admin.ModelAdmin):
    """Admin interface for CorpusMetadata model."""
    
    list_display = [
        'document', 
        'source_format', 
        'sentence_count', 
        'unique_forms',
        'unique_lemmas',
        'imported_at',
        'imported_by'
    ]
    list_filter = ['source_format', 'imported_at']
    search_fields = ['document__filename', 'original_filename']
    readonly_fields = [
        'document', 'source_format', 'global_metadata', 'structural_annotations',
        'imported_at', 'imported_by', 'original_filename', 'file_hash',
        'sentence_count', 'unique_lemmas', 'unique_forms'
    ]
    
    fieldsets = (
        ('Document Info', {
            'fields': ('document', 'source_format', 'original_filename')
        }),
        ('Metadata', {
            'fields': ('global_metadata', 'structural_annotations')
        }),
        ('Statistics', {
            'fields': ('sentence_count', 'unique_forms', 'unique_lemmas')
        }),
        ('Import Tracking', {
            'fields': ('imported_at', 'imported_by', 'file_hash')
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Metadata created via import only
    
    def has_change_permission(self, request, obj=None):
        return True  # View only
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
