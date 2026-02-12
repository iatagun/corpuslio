"""Models for advanced corpus features."""

from django.db import models
from django.conf import settings
from .models import Document


class Collection(models.Model):
    """Subcorpus collection for grouping documents."""
    
    name = models.CharField(max_length=200, verbose_name="Koleksiyon Adı")
    description = models.TextField(blank=True, verbose_name="Açıklama")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='collections',
        null=True,
        blank=True,
        verbose_name="Sahip"
    )
    documents = models.ManyToManyField(
        Document,
        related_name='collections',
        verbose_name="Belgeler"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    
    class Meta:
        verbose_name = "Koleksiyon"
        verbose_name_plural = "Koleksiyonlar"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_document_count(self):
        """Get number of documents in collection."""
        return self.documents.count()
    
    def get_total_words(self):
        """Get total word count across all documents."""
        total = 0
        for doc in self.documents.all():
            total += doc.get_word_count()
        return total

    @property
    def document_count(self):
        """Compatibility property for templates expecting `document_count`."""
        return self.get_document_count()

    @property
    def total_words(self):
        """Compatibility property for templates expecting `total_words`."""
        return self.get_total_words()


class QueryHistory(models.Model):
    """Store user's search queries for history and favorites."""
    
    QUERY_TYPES = [
        ('kwic', 'KWIC'),
        ('ngram', 'N-gram'),
        ('advanced', 'Advanced'),
    ]
    
    query_text = models.CharField(max_length=500, verbose_name="Sorgu")
    query_type = models.CharField(
        max_length=20,
        choices=QUERY_TYPES,
        default='kwic',
        verbose_name="Sorgu Tipi"
    )
    parameters = models.JSONField(default=dict, verbose_name="Parametreler")
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Belge"
    )
    is_favorite = models.BooleanField(default=False, verbose_name="Favori mi?")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    
    class Meta:
        verbose_name = "Sorgu Geçmişi"
        verbose_name_plural = "Sorgu Geçmişleri"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.query_type}: {self.query_text[:50]}"
