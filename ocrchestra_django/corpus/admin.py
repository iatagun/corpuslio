"""Admin panel configuration for corpus models."""

from django.contrib import admin
from .models import Document, Content, Analysis, ProcessingTask


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin interface for Document model."""
    
    list_display = ['filename', 'format', 'upload_date', 'processed', 'get_word_count']
    list_filter = ['processed', 'format', 'upload_date']
    search_fields = ['filename']
    readonly_fields = ['upload_date']
    
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
from .collections import Collection, QueryHistory

admin.site.register(Collection)
admin.site.register(QueryHistory)
