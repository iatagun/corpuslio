"""Django models for OCRchestra corpus management."""

from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Extended user profile for corpus platform access control.
    
    Implements 5-tier role system:
    - ANONYMOUS: No account, limited public access
    - REGISTERED: Email-verified, basic export rights
    - VERIFIED: Academic researcher, full query + API access
    - DEVELOPER: API integration projects
    - ADMIN: Platform management
    """
    
    ROLE_CHOICES = [
        ('anonymous', 'Anonim Kullanıcı'),  # Not in DB, conceptual
        ('registered', 'Kayıtlı Kullanıcı'),
        ('verified', 'Doğrulanmış Araştırmacı'),
        ('developer', 'Geliştirici (API Erişimi)'),
        ('admin', 'Sistem Yöneticisi'),
    ]
    
    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Beklemede'),
        ('approved', 'Onaylandı'),
        ('rejected', 'Reddedildi'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="Kullanıcı"
    )
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='registered',
        verbose_name="Rol"
    )
    
    # Verification fields for VERIFIED role
    institution = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Kurum"
    )
    orcid = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="ORCID ID",
        help_text="ORCID kimliği (örn: 0000-0002-1234-5678)"
    )
    research_purpose = models.TextField(
        blank=True,
        verbose_name="Araştırma Amacı",
        help_text="Korpusu neden kullanmak istiyorsunuz?"
    )
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='pending',
        verbose_name="Doğrulama Durumu"
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Doğrulama Tarihi"
    )
    verified_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='verified_users',
        verbose_name="Doğrulayan Admin"
    )
    
    # API access for DEVELOPER role
    api_key = models.CharField(
        max_length=64,
        blank=True,
        unique=True,
        null=True,
        verbose_name="API Anahtarı"
    )
    api_quota_daily = models.IntegerField(
        default=1000,
        verbose_name="Günlük API Kotası"
    )
    api_calls_today = models.IntegerField(
        default=0,
        verbose_name="Bugünkü API Çağrıları"
    )
    api_last_reset = models.DateField(
        auto_now_add=True,
        verbose_name="API Sayacı Sıfırlama"
    )
    
    # Export quotas
    export_quota_mb = models.IntegerField(
        default=5,
        verbose_name="Aylık Export Kotası (MB)",
        help_text="Registered: 5MB, Verified: 100MB"
    )
    export_used_mb = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Kullanılan Export (MB)"
    )
    export_last_reset = models.DateField(
        auto_now_add=True,
        verbose_name="Export Sayacı Sıfırlama"
    )
    
    # Query limits
    queries_today = models.IntegerField(
        default=0,
        verbose_name="Bugünkü Sorgular"
    )
    query_last_reset = models.DateField(
        auto_now_add=True,
        verbose_name="Sorgu Sayacı Sıfırlama"
    )
    
    # Terms acceptance
    terms_accepted = models.BooleanField(
        default=False,
        verbose_name="Kullanım Koşulları Kabul Edildi"
    )
    terms_accepted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Koşulların Kabul Tarihi"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Kayıt Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")
    
    class Meta:
        verbose_name = "Kullanıcı Profili"
        verbose_name_plural = "Kullanıcı Profilleri"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
    
    def get_query_limit(self):
        """Get daily query limit based on role."""
        # Superusers have unlimited queries
        if self.user.is_superuser:
            return 0  # unlimited
        
        limits = {
            'registered': 100,
            'verified': 1000,
            'developer': 0,  # unlimited (rate-limited by API)
            'admin': 0,      # unlimited
        }
        return limits.get(self.role, 10)  # Default 10 for others
    
    def can_query(self):
        """Check if user can make more queries today."""
        # Superusers always can query
        if self.user.is_superuser:
            return True
        
        limit = self.get_query_limit()
        if limit == 0:  # unlimited
            return True
        return self.queries_today < limit
    
    def can_export(self, size_mb=0):
        """Check if user has export quota left."""
        # Superusers have unlimited export quota
        if self.user.is_superuser:
            return True
        
        return (self.export_used_mb + size_mb) <= self.export_quota_mb
    
    def increment_query_count(self):
        """Increment today's query count with automatic daily reset."""
        from datetime import date
        today = date.today()
        
        # Reset if new day
        if self.query_last_reset < today:
            self.queries_today = 0
            self.query_last_reset = today
        
        self.queries_today += 1
        self.save(update_fields=['queries_today', 'query_last_reset'])
    
    def reset_query_count_if_needed(self):
        """Check and reset query count if it's a new day."""
        from datetime import date
        today = date.today()
        
        if self.query_last_reset < today:
            self.queries_today = 0
            self.query_last_reset = today
            self.save(update_fields=['queries_today', 'query_last_reset'])
    
    def use_export_quota(self, size_mb):
        """Deduct from export quota with automatic monthly reset."""
        from datetime import date
        
        today = date.today()
        
        # Reset if new month
        if self.export_last_reset.month != today.month or self.export_last_reset.year != today.year:
            self.export_used_mb = Decimal('0.00')
            self.export_last_reset = today
        
        self.export_used_mb += Decimal(str(size_mb))
        self.save(update_fields=['export_used_mb', 'export_last_reset'])
    
    def reset_export_quota_if_needed(self):
        """Check and reset export quota if it's a new month."""
        from datetime import date
        
        today = date.today()
        
        if self.export_last_reset.month != today.month or self.export_last_reset.year != today.year:
            self.export_used_mb = Decimal('0.00')
            self.export_last_reset = today
            self.save(update_fields=['export_used_mb', 'export_last_reset'])
    
    def generate_api_key(self):
        """Generate unique API key for developer role."""
        import secrets
        self.api_key = secrets.token_urlsafe(48)
        self.save(update_fields=['api_key'])
        return self.api_key
    
    def is_verified_researcher(self):
        """Check if user is verified researcher or higher."""
        return self.role in ['verified', 'developer', 'admin']
    
    def is_developer(self):
        """Check if user has API access."""
        return self.role in ['developer', 'admin']
    
    def is_admin(self):
        """Check if user is admin."""
        return self.role == 'admin' or self.user.is_staff


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create profile when user registers."""
    if created:
        # Determine initial role based on user status
        initial_role = 'admin' if instance.is_superuser else 'registered'
        UserProfile.objects.create(user=instance, role=initial_role)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save profile when user is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()


class Tag(models.Model):
    """Tag model for categorizing documents."""
    
    COLOR_CHOICES = [
        ('blue', 'Mavi'),
        ('green', 'Yeşil'),
        ('red', 'Kırmızı'),
        ('yellow', 'Sarı'),
        ('purple', 'Mor'),
        ('pink', 'Pembe'),
        ('orange', 'Turuncu'),
        ('teal', 'Turkuaz'),
    ]
    
    name = models.CharField(max_length=50, unique=True, verbose_name="Etiket Adı")
    slug = models.SlugField(max_length=50, unique=True, verbose_name="Slug")
    color = models.CharField(
        max_length=20, 
        choices=COLOR_CHOICES, 
        default='blue',
        verbose_name="Renk"
    )
    description = models.TextField(blank=True, verbose_name="Açıklama")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    
    class Meta:
        ordering = ['name']
        verbose_name = "Etiket"
        verbose_name_plural = "Etiketler"
    
    def __str__(self):
        return self.name
    
    def get_document_count(self):
        """Get number of documents with this tag."""
        return self.documents.count()


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
    
    # Tags (Many-to-Many relationship)
    tags = models.ManyToManyField(
        Tag,
        related_name='documents',
        blank=True,
        verbose_name="Etiketler"
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


class SearchHistory(models.Model):
    """Search history tracking for users."""
    
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='search_history',
        verbose_name="Kullanıcı"
    )
    query = models.CharField(max_length=500, verbose_name="Arama Sorgusu")
    search_type = models.CharField(
        max_length=20,
        choices=[
            ('basic', 'Basit'),
            ('fuzzy', 'Benzer'),
            ('regex', 'Regex'),
            ('advanced', 'Gelişmiş'),
        ],
        default='basic',
        verbose_name="Arama Tipi"
    )
    filters = models.JSONField(default=dict, blank=True, verbose_name="Filtreler")
    result_count = models.IntegerField(default=0, verbose_name="Sonuç Sayısı")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Tarih")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Arama Geçmişi"
        verbose_name_plural = "Arama Geçmişleri"
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username}: {self.query} ({self.created_at.strftime('%d.%m.%Y %H:%M')})"


class QueryLog(models.Model):
    """
    Detailed query audit log for platform monitoring and analytics.
    
    Tracks all corpus queries with detailed metadata for:
    - Abuse prevention (rate limiting enforcement)
    - Usage analytics (popular queries, performance metrics)
    - Research insights (query patterns, user behavior)
    - Compliance (KVKK/GDPR audit trail)
    """
    
    # User information
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='query_logs',
        verbose_name="Kullanıcı",
        help_text="Authenticated user (null for anonymous)"
    )
    session_key = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        verbose_name="Oturum Anahtarı",
        help_text="Django session key for anonymous user tracking"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP Adresi"
    )
    user_agent = models.CharField(
        max_length=256,
        blank=True,
        verbose_name="User Agent"
    )
    
    # Query details
    query_text = models.TextField(verbose_name="Sorgu Metni")
    query_type = models.CharField(
        max_length=20,
        choices=[
            ('word', 'Kelime'),
            ('lemma', 'Kök'),
            ('pos', 'POS Tag'),
            ('advanced', 'Gelişmiş'),
            ('concordance', 'Konkordans'),
            ('frequency', 'Frekans'),
            ('ngram', 'N-gram'),
        ],
        verbose_name="Sorgu Tipi"
    )
    document = models.ForeignKey(
        'Document',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='query_logs',
        verbose_name="Doküman"
    )
    filters_applied = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Uygulanan Filtreler",
        help_text="Case sensitivity, regex, context size, etc."
    )
    
    # Results
    result_count = models.IntegerField(
        default=0,
        verbose_name="Sonuç Sayısı"
    )
    execution_time_ms = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="İşlem Süresi (ms)",
        help_text="Query execution time in milliseconds"
    )
    is_cached = models.BooleanField(
        default=False,
        verbose_name="Önbellekten",
        help_text="Whether results were served from cache"
    )
    
    # Rate limiting
    rate_limit_hit = models.BooleanField(
        default=False,
        verbose_name="Limit Aşıldı",
        help_text="Query blocked due to rate limit"
    )
    daily_query_count = models.IntegerField(
        default=1,
        verbose_name="Günlük Sorgu Sayısı",
        help_text="User's query count when this query was made"
    )
    
    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Tarih",
        db_index=True
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Sorgu Logu"
        verbose_name_plural = "Sorgu Logları"
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['ip_address', '-created_at']),
            models.Index(fields=['query_type', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        user_str = self.user.username if self.user else f"Anonymous ({self.ip_address})"
        return f"{user_str}: {self.query_text[:50]} - {self.result_count} results"


class ExportLog(models.Model):
    """
    Export activity audit log for quota enforcement and compliance.
    
    Tracks all data exports with:
    - Export quota tracking (MB per month)
    - Format and content verification
    - Watermark injection record
    - Download tracking
    """
    
    # User information
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,  # Never delete export logs
        related_name='export_logs',
        verbose_name="Kullanıcı"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP Adresi"
    )
    
    # Export details
    export_type = models.CharField(
        max_length=20,
        choices=[
            ('concordance', 'Konkordans'),
            ('frequency', 'Frekans Listesi'),
            ('document', 'Tam Doküman'),
            ('analysis', 'Analiz Sonuçları'),
            ('statistics', 'İstatistikler'),
        ],
        verbose_name="Export Tipi"
    )
    format = models.CharField(
        max_length=10,
        choices=[
            ('csv', 'CSV'),
            ('json', 'JSON'),
            ('conllu', 'CoNLL-U'),
            ('txt', 'Text'),
            ('xlsx', 'Excel'),
            ('pdf', 'PDF'),
        ],
        verbose_name="Format"
    )
    
    # Content metadata
    document = models.ForeignKey(
        'Document',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='export_logs',
        verbose_name="Doküman"
    )
    query_text = models.TextField(
        blank=True,
        verbose_name="İlgili Sorgu",
        help_text="Query that generated the exported data"
    )
    row_count = models.IntegerField(
        default=0,
        verbose_name="Satır Sayısı",
        help_text="Number of rows/records exported"
    )
    file_size_bytes = models.BigIntegerField(
        default=0,
        verbose_name="Dosya Boyutu (byte)"
    )
    file_size_mb = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Dosya Boyutu (MB)"
    )
    
    # Watermark & citation
    watermark_applied = models.BooleanField(
        default=True,
        verbose_name="Filigran Eklendi",
        help_text="Whether export includes platform watermark"
    )
    citation_text = models.TextField(
        blank=True,
        verbose_name="Atıf Metni",
        help_text="Citation text included in export"
    )
    
    # Download tracking
    download_count = models.IntegerField(
        default=0,
        verbose_name="İndirme Sayısı",
        help_text="How many times file was downloaded"
    )
    last_downloaded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Son İndirme"
    )
    file_path = models.CharField(
        max_length=512,
        blank=True,
        verbose_name="Dosya Yolu",
        help_text="Storage path for generated file"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Geçerlilik Süresi",
        help_text="Export file auto-delete date (30 days default)"
    )
    
    # Quota tracking
    quota_before_mb = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Önceki Kota (MB)"
    )
    quota_after_mb = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Sonraki Kota (MB)"
    )
    
    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Oluşturulma",
        db_index=True
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Export Logu"
        verbose_name_plural = "Export Logları"
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['export_type', 'format']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username}: {self.export_type} ({self.format}) - {self.file_size_mb} MB"
    
    def save(self, *args, **kwargs):
        """Auto-calculate file_size_mb from file_size_bytes."""
        if self.file_size_bytes > 0:
            self.file_size_mb = Decimal(self.file_size_bytes) / Decimal(1024 * 1024)
        super().save(*args, **kwargs)

