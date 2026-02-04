"""Django models for OCRchestra corpus management."""

from django.db import models
from django.utils import timezone


class Document(models.Model):
    """Document model for uploaded files."""
    
    filename = models.CharField(max_length=255, verbose_name="Dosya Adı")
    file = models.FileField(upload_to='documents/%Y/%m/', verbose_name="Dosya")
    format = models.CharField(max_length=10, verbose_name="Format")
    upload_date = models.DateTimeField(default=timezone.now, verbose_name="Yüklenme Tarihi")
    processed = models.BooleanField(default=False, verbose_name="İşlendi mi?")
    # Core Metadata Fields (Promoted from JSON)
    author = models.CharField(max_length=255, blank=True, verbose_name="Yazar")
    genre = models.CharField(max_length=100, blank=True, verbose_name="Tür")
    language = models.CharField(max_length=10, default='tr', verbose_name="Dil")
    source = models.CharField(max_length=255, blank=True, verbose_name="Kaynak")

    # MEB - Söz Varlığı Projesi Metadata Fields
    GRADE_LEVEL_CHOICES = [
        ('PRE', 'Okul Öncesi'),
        ('1', '1. Sınıf'),
        ('2', '2. Sınıf'),
        ('3', '3. Sınıf'),
        ('4', '4. Sınıf'),
        ('5', '5. Sınıf'),
        ('6', '6. Sınıf'),
        ('7', '7. Sınıf'),
        ('8', '8. Sınıf'),
        ('9', '9. Sınıf'),
        ('10', '10. Sınıf'),
        ('11', '11. Sınıf'),
        ('12', '12. Sınıf'),
        ('UNI', 'Üniversite/Akademik'),
        ('GEN', 'Genel/Yetişkin'),
    ]

    grade_level = models.CharField(
        max_length=10, 
        choices=GRADE_LEVEL_CHOICES, 
        blank=True, 
        null=True, 
        verbose_name="Sınıf Seviyesi"
    )
    subject = models.CharField(max_length=100, blank=True, verbose_name="Ders/Alan")
    publisher = models.CharField(max_length=255, blank=True, verbose_name="Yayınevi")
    publication_year = models.IntegerField(null=True, blank=True, verbose_name="Basım Yılı")
    isbn = models.CharField(max_length=20, blank=True, verbose_name="ISBN")

    # Legacy metadata (kept for backward compatibility & extra fields)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Ek Metadata",
        help_text="Diğer detaylar (JSON)"
    )
    
    class Meta:
        ordering = ['-upload_date']
        verbose_name = "Belge"
        verbose_name_plural = "Belgeler"
    
    def __str__(self):
        return f"{self.filename} ({self.format})"
    
    def get_word_count(self):
        """Get word count from cleaned text."""
        if hasattr(self, 'content') and self.content.cleaned_text:
            return len(self.content.cleaned_text.split())
        return 0
    
    def get_metadata_display(self):
        """Get formatted metadata for display."""
        if not self.metadata:
            return {}
        
        return {
            'Yazar': self.metadata.get('author', '-'),
            'Tarih': self.metadata.get('date', '-'),
            'Kaynak': self.metadata.get('source', '-'),
            'Tür': self.metadata.get('genre', '-'),
            'Dil': self.metadata.get('language', 'tr'),
            'Yayınevi': self.metadata.get('publisher', '-'),
        }



class Content(models.Model):
    """Text content extracted from document."""
    
    document = models.OneToOneField(
        Document, 
        on_delete=models.CASCADE, 
        related_name='content',
        verbose_name="Belge"
    )
    raw_text = models.TextField(blank=True, verbose_name="Ham Metin")
    cleaned_text = models.TextField(blank=True, verbose_name="Temiz Metin")
    
    class Meta:
        verbose_name = "İçerik"
        verbose_name_plural = "İçerikler"
    
    def __str__(self):
        return f"İçerik: {self.document.filename}"


class Analysis(models.Model):
    """Linguistic analysis data (POS, lemma, morphology)."""
    
    document = models.OneToOneField(
        Document, 
        on_delete=models.CASCADE, 
        related_name='analysis',
        verbose_name="Belge"
    )
    data = models.JSONField(default=list, verbose_name="Analiz Verisi")
    analyzed_at = models.DateTimeField(auto_now=True, verbose_name="Analiz Tarihi")
    
    class Meta:
        verbose_name = "Analiz"
        verbose_name_plural = "Analizler"
    
    def __str__(self):
        return f"Analiz: {self.document.filename}"
    
    def get_word_count(self):
        """Get total words analyzed."""
        return len(self.data) if self.data else 0
    
    def get_pos_distribution(self):
        """Get POS tag distribution."""
        from collections import Counter
        if not self.data:
            return {}
        
        pos_tags = [item.get('pos', 'UNKNOWN') for item in self.data if isinstance(item, dict)]
        return dict(Counter(pos_tags))


class ProcessingTask(models.Model):
    """Track async processing tasks (Celery)."""
    
    STATUS_CHOICES = [
        ('PENDING', 'Bekliyor'),
        ('PROCESSING', 'İşleniyor'),
        ('COMPLETED', 'Tamamlandı'),
        ('FAILED', 'Başarısız'),
    ]
    
    document = models.ForeignKey(
        Document, 
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name="Belge"
    )
    task_id = models.CharField(max_length=255, unique=True, verbose_name="Görev ID")
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PENDING',
        verbose_name="Durum"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")
    error_message = models.TextField(blank=True, verbose_name="Hata Mesajı")
    progress = models.IntegerField(default=0, verbose_name="İlerleme %")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "İşlem Görevi"
        verbose_name_plural = "İşlem Görevleri"
    
    def __str__(self):
        return f"{self.document.filename} - {self.status}"
