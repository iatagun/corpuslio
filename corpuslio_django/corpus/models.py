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
        default=10,
        verbose_name="Aylık Export Kotası (MB)",
        help_text="Registered: 10MB, Verified: 100MB, Developer: 500MB"
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
    
    # Email verification (Task 11.1)
    email_verified = models.BooleanField(
        default=False,
        verbose_name="Email Doğrulandı",
        help_text="Kullanıcı email adresini doğruladı mı?"
    )
    email_verification_token = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        unique=True,
        verbose_name="Email Doğrulama Token",
        help_text="Email doğrulama için benzersiz token"
    )
    email_verification_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Doğrulama Emaili Gönderilme Zamanı"
    )
    email_token_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Token Geçerlilik Süresi",
        help_text="Token 24 saat geçerlidir"
    )
    
    # Login security (Task 11.9)
    failed_login_attempts = models.IntegerField(
        default=0,
        verbose_name="Başarısız Giriş Denemeleri"
    )
    last_failed_login = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Son Başarısız Giriş"
    )
    account_locked_until = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Hesap Kilitli (Süre)",
        help_text="5 başarısız denemeden sonra 30 dakika kilitlenir"
    )
    
    # Password reset (Task 11.12)
    password_reset_token = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        unique=True,
        verbose_name="Şifre Sıfırlama Token",
        help_text="Şifre sıfırlama için benzersiz token"
    )
    password_reset_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Sıfırlama Emaili Gönderilme Zamanı"
    )
    password_reset_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Reset Token Geçerlilik Süresi",
        help_text="Token 1 saat geçerlidir"
    )
    
    # Export preferences
    enable_watermark = models.BooleanField(
        default=True,
        verbose_name="Export'larda Filigran Ekle",
        help_text="Export edilen dosyalarda CorpusLIO atıf bilgisi gösterilsin mi?"
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
        """Get daily query limit based on role.
        
        Role-based limits:
        - registered: 100 queries/day (basic access)
        - verified: 1000 queries/day (researcher tier)
        - developer: 10000 queries/day (API tier)
        - admin: unlimited
        """
        # Superusers have unlimited queries
        if self.user.is_superuser:
            return 0  # unlimited
        
        limits = {
            'registered': 100,
            'verified': 1000,
            'developer': 10000,
            'admin': 0,      # unlimited
        }
        return limits.get(self.role, 50)  # Default 50 for others
    
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
        
        # Get role-based quota
        quota = self.get_export_quota()
        if quota == 0:  # unlimited
            return True
            
        return (self.export_used_mb + size_mb) <= quota
    
    def get_export_quota(self):
        """Get monthly export quota (MB) based on role.
        
        Role-based quotas:
        - registered: 10 MB/month (basic tier)
        - verified: 100 MB/month (researcher tier)
        - developer: 500 MB/month (API tier)
        - admin: unlimited
        """
        if self.user.is_superuser:
            return 0  # unlimited
        
        quotas = {
            'registered': 10,
            'verified': 100,
            'developer': 500,
            'admin': 0,  # unlimited
        }
        return quotas.get(self.role, 5)  # Default 5MB for others
    
    def update_quota_for_role(self):
        """Update export_quota_mb when role changes."""
        new_quota = self.get_export_quota()
        if new_quota != 0:  # Don't update if unlimited
            self.export_quota_mb = new_quota
            self.save(update_fields=['export_quota_mb'])
    
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

        # Ensure size_mb is a Decimal and round up to 2 decimal places
        try:
            from decimal import ROUND_UP
            delta = Decimal(str(size_mb))
            if delta > 0:
                # charge at least 0.01 MB granularity
                delta = delta.quantize(Decimal('0.01'), rounding=ROUND_UP)
            else:
                delta = Decimal('0.00')
        except Exception:
            delta = Decimal('0.00')

        self.export_used_mb += delta
        self.save(update_fields=['export_used_mb', 'export_last_reset'])
    
    def reset_export_quota_if_needed(self):
        """Check and reset export quota if it's a new month."""
        from datetime import date
        
        today = date.today()
        
        if self.export_last_reset.month != today.month or self.export_last_reset.year != today.year:
            self.export_used_mb = Decimal('0.00')
            self.export_last_reset = today
            self.save(update_fields=['export_used_mb', 'export_last_reset'])
    
    # Email Verification Methods (Task 11.1)
    def generate_verification_token(self):
        """Generate a unique email verification token with 24-hour expiration."""
        import uuid
        from datetime import timedelta
        
        self.email_verification_token = uuid.uuid4().hex
        self.email_verification_sent_at = timezone.now()
        self.email_token_expires_at = timezone.now() + timedelta(hours=24)
        self.save(update_fields=['email_verification_token', 'email_verification_sent_at', 'email_token_expires_at'])
        return self.email_verification_token
    
    def is_email_token_valid(self):
        """Check if email verification token is valid (exists and not expired)."""
        if not self.email_verification_token:
            return False
        
        if not self.email_token_expires_at:
            return False
        
        # Check if token expired
        if timezone.now() > self.email_token_expires_at:
            return False
        
        return True
    
    def mark_email_verified(self):
        """Mark email as verified and activate user account."""
        self.email_verified = True
        self.email_verification_token = None
        self.email_verification_sent_at = None
        self.email_token_expires_at = None
        
        # Activate user account
        if not self.user.is_active:
            self.user.is_active = True
            self.user.save(update_fields=['is_active'])
        
        self.save(update_fields=['email_verified', 'email_verification_token', 
                                 'email_verification_sent_at', 'email_token_expires_at'])
    
    # Login Security Methods (Task 11.9)
    def is_account_locked(self):
        """Check if account is currently locked due to failed login attempts."""
        if not self.account_locked_until:
            return False
        
        # Check if lock period has passed
        if timezone.now() > self.account_locked_until:
            # Unlock account
            self.account_locked_until = None
            self.failed_login_attempts = 0
            self.save(update_fields=['account_locked_until', 'failed_login_attempts'])
            return False
        
        return True
    
    def record_failed_login(self):
        """Record a failed login attempt and lock account if threshold reached."""
        from datetime import timedelta
        
        self.failed_login_attempts += 1
        self.last_failed_login = timezone.now()
        
        # Lock account after 5 failed attempts for 30 minutes
        if self.failed_login_attempts >= 5:
            self.account_locked_until = timezone.now() + timedelta(minutes=30)
        
        self.save(update_fields=['failed_login_attempts', 'last_failed_login', 'account_locked_until'])
    
    def reset_failed_login_attempts(self):
        """Reset failed login counter after successful login."""
        self.failed_login_attempts = 0
        self.last_failed_login = None
        self.account_locked_until = None
        self.save(update_fields=['failed_login_attempts', 'last_failed_login', 'account_locked_until'])
    
    # Password Reset Methods (Task 11.12)
    def generate_password_reset_token(self):
        """Generate a unique password reset token with 1-hour expiration."""
        import uuid
        from datetime import timedelta
        
        self.password_reset_token = uuid.uuid4().hex
        self.password_reset_sent_at = timezone.now()
        self.password_reset_expires_at = timezone.now() + timedelta(hours=1)
        self.save(update_fields=['password_reset_token', 'password_reset_sent_at', 'password_reset_expires_at'])
        return self.password_reset_token
    
    def is_reset_token_valid(self):
        """Check if password reset token is valid (exists and not expired)."""
        if not self.password_reset_token:
            return False
        
        if not self.password_reset_expires_at:
            return False
        
        # Check if token expired (1 hour)
        if timezone.now() > self.password_reset_expires_at:
            return False
        
        return True
    
    def clear_reset_token(self):
        """Clear password reset token after successful reset or expiration."""
        self.password_reset_token = None
        self.password_reset_sent_at = None
        self.password_reset_expires_at = None
        self.save(update_fields=['password_reset_token', 'password_reset_sent_at', 'password_reset_expires_at'])

    def get_export_quota_mb(self):
        """Return the user's monthly export quota in MB.

        Returns 0 to indicate 'unlimited' for superusers or roles configured as unlimited.
        """
        # Superusers have unlimited quota
        if self.user.is_superuser:
            return 0

        try:
            return int(self.export_quota_mb or 0)
        except Exception:
            return 0
    
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


class LoginHistory(models.Model):
    """Track user login attempts for security monitoring (Task 11.15)."""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='login_history',
        null=True,
        blank=True,
        verbose_name="Kullanıcı",
        help_text="Null ise başarısız login attempt (user bulunamadı)"
    )
    
    username_attempted = models.CharField(
        max_length=150,
        verbose_name="Denenen Kullanıcı Adı",
        help_text="Girilen username/email"
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Giriş Zamanı",
        db_index=True
    )
    
    ip_address = models.GenericIPAddressField(
        verbose_name="IP Adresi"
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent",
        help_text="Browser/device bilgisi"
    )
    
    success = models.BooleanField(
        default=True,
        verbose_name="Başarılı mı?",
        db_index=True
    )
    
    failure_reason = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Başarısızlık Nedeni",
        help_text="Örn: invalid_credentials, account_locked, email_not_verified"
    )
    
    session_key = models.CharField(
        max_length=40,
        blank=True,
        verbose_name="Session Key",
        help_text="Django session key (başarılı login için)"
    )
    
    is_suspicious = models.BooleanField(
        default=False,
        verbose_name="Şüpheli Aktivite",
        db_index=True,
        help_text="Otomatik tespit edilen şüpheli aktivite"
    )
    
    # Device/Browser info (parsed from user_agent)
    device_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Cihaz Tipi",
        help_text="Desktop, Mobile, Tablet, Bot"
    )
    
    browser = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Tarayıcı"
    )
    
    os = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="İşletim Sistemi"
    )
    
    # Location (optional, from IP geolocation)
    location_city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Şehir"
    )
    
    location_country = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Ülke"
    )
    
    class Meta:
        verbose_name = "Login Geçmişi"
        verbose_name_plural = "Login Geçmişi Kayıtları"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp', 'user']),
            models.Index(fields=['ip_address', '-timestamp']),
            models.Index(fields=['is_suspicious', '-timestamp']),
        ]
    
    def __str__(self):
        status = "✓ Başarılı" if self.success else "✗ Başarısız"
        username = self.user.username if self.user else self.username_attempted
        return f"{username} - {status} - {self.timestamp.strftime('%d.%m.%Y %H:%M')}"
    
    def get_device_info(self):
        """Return formatted device info string."""
        parts = []
        if self.device_type:
            parts.append(self.device_type)
        if self.browser:
            parts.append(self.browser)
        if self.os:
            parts.append(self.os)
        return " • ".join(parts) if parts else "Bilinmiyor"
    
    def get_location(self):
        """Return formatted location string."""
        if self.location_city and self.location_country:
            return f"{self.location_city}, {self.location_country}"
        elif self.location_country:
            return self.location_country
        return "Bilinmiyor"


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

    # Corpus Linguistics Metadata Fields (Week 5)
    TEXT_TYPE_CHOICES = [
        ('written', 'Yazılı'),
        ('spoken', 'Sözlü'),
        ('mixed', 'Karma'),
        ('web', 'Web/Dijital'),
    ]
    
    text_type = models.CharField(
        max_length=20,
        choices=TEXT_TYPE_CHOICES,
        default='written',
        verbose_name="Metin Türü",
        help_text="Yazılı, sözlü veya karma metin"
    )
    
    LICENSE_CHOICES = [
        ('public_domain', 'Kamu Malı'),
        ('cc_by', 'CC BY - İsim Belirtme'),
        ('cc_by_sa', 'CC BY-SA - Aynı Lisansla Paylaşım'),
        ('cc_by_nc', 'CC BY-NC - Ticari Olmayan'),
        ('cc_by_nc_sa', 'CC BY-NC-SA - Ticari Olmayan, Aynı Lisansla'),
        ('educational', 'Eğitim Amaçlı Kullanım'),
        ('copyright', 'Telif Hakkı Korumalı'),
        ('unknown', 'Bilinmiyor'),
    ]
    
    license = models.CharField(
        max_length=30,
        choices=LICENSE_CHOICES,
        default='unknown',
        verbose_name="Lisans",
        help_text="Belgenin kullanım lisansı"
    )
    
    region = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Bölge/Lehçe",
        help_text="Coğrafi köken (örn: İstanbul, Anadolu, Rumeli)"
    )
    
    collection = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Koleksiyon",
        help_text="Alt küme kategorisi (örn: Modern Türk Edebiyatı, Basın Metinleri)"
    )
    
    token_count = models.IntegerField(
        default=0,
        verbose_name="Token Sayısı",
        help_text="Otomatik hesaplanan kelime/token sayısı"
    )
    
    document_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Belge Tarihi",
        help_text="Metnin gerçek oluşturulma tarihi (yükleme tarihinden farklı)"
    )
    
    # Privacy & Anonymization Fields (Week 6)
    PRIVACY_STATUS_CHOICES = [
        ('raw', 'Ham Veri (İşlenmemiş)'),
        ('anonymized', 'Anonimleştirilmiş'),
        ('pseudonymized', 'Sözde Anonimleştirilmiş'),
        ('public', 'Genel Kullanıma Açık'),
    ]
    
    privacy_status = models.CharField(
        max_length=20,
        choices=PRIVACY_STATUS_CHOICES,
        default='raw',
        verbose_name="Gizlilik Durumu",
        help_text="Belgenin anonimleştirme durumu"
    )
    
    anonymized_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Anonimleştirme Tarihi",
        help_text="Belgenin anonimleştirildiği tarih"
    )
    
    anonymization_report = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Anonimleştirme Raporu",
        help_text="Maskelenen varlıkların detayları (PERSON: 5, EMAIL: 2, vb.)"
    )
    
    contains_personal_data = models.BooleanField(
        default=False,
        verbose_name="Kişisel Veri İçeriyor",
        help_text="Belgede tespit edilen kişisel veri var mı?"
    )

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
            count = len(self.content.cleaned_text.split())
            # Update token_count if different
            if self.token_count != count:
                self.token_count = count
                self.save(update_fields=['token_count'])
            return count
        return self.token_count  # Return stored value if no content
    
    def update_token_count(self):
        """Update token count from content."""
        if hasattr(self, 'content') and self.content.cleaned_text:
            self.token_count = len(self.content.cleaned_text.split())
            self.save(update_fields=['token_count'])
    
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
        verbose_name="Doküman"
    )
    raw_text = models.TextField(blank=True, verbose_name="Ham Metin")
    cleaned_text = models.TextField(blank=True, verbose_name="Temiz Metin")
    
    class Meta:
        verbose_name = "İçerik"
        verbose_name_plural = "İçerikler"
    
    def __str__(self):
        return f"İçerik: {self.document.filename}"


class Analysis(models.Model):
    """Linguistic analysis data (POS, lemma, morphology, dependencies)."""
    
    document = models.OneToOneField(
        Document, 
        on_delete=models.CASCADE, 
        related_name='analysis',
        verbose_name="Belge"
    )
    data = models.JSONField(default=list, verbose_name="Analiz Verisi")
    analyzed_at = models.DateTimeField(auto_now=True, verbose_name="Analiz Tarihi")
    
    # CoNLL-U / Dependency Parsing Support (Week 4)
    conllu_data = models.JSONField(
        default=list,
        null=True,
        blank=True,
        verbose_name="CoNLL-U Verisi",
        help_text="Bağımlılık ayrıştırma verileri (10 sütunlu CoNLL-U formatı)"
    )
    has_dependencies = models.BooleanField(
        default=False,
        verbose_name="Bağımlılık Verisi Var",
        help_text="Bu belgenin bağımlılık ayrıştırma verisi var mı?"
    )
    dependency_parser = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name="Bağımlılık Ayrıştırıcı",
        help_text="Kullanılan ayrıştırıcı (örn: 'stanza-tr', 'spaCy-tr')"
    )
    
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
    
    def get_dependency_count(self):
        """Get total dependency relations."""
        if not self.has_dependencies or not self.conllu_data:
            return 0
        return len(self.conllu_data)
    
    def get_dependency_relations(self):
        """Get distribution of dependency relations."""
        from collections import Counter
        if not self.has_dependencies or not self.conllu_data:
            return {}
        
        deprels = [token.get('deprel', 'UNKNOWN') 
                   for token in self.conllu_data 
                   if isinstance(token, dict)]
        return dict(Counter(deprels))


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
    document_title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Doküman Adı (Snapshot)",
        help_text="Belge silinse bile adını saklar"
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


# ============================================================
# KVKK/GDPR COMPLIANCE MODELS (Week 11)
# ============================================================

class DataExportRequest(models.Model):
    """
    User data export requests (KVKK/GDPR compliance).
    
    Users have the right to request all their personal data
    in a portable format (JSON or CSV).
    """
    
    STATUS_CHOICES = [
        ('pending', 'Beklemede'),
        ('processing', 'İşleniyor'),
        ('completed', 'Tamamlandı'),
        ('failed', 'Başarısız'),
        ('expired', 'Süresi Doldu'),
    ]
    
    FORMAT_CHOICES = [
        ('json', 'JSON'),
        ('csv', 'CSV'),
        ('both', 'Both (JSON + CSV)'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='data_export_requests',
        verbose_name="Kullanıcı"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Durum",
        db_index=True
    )
    
    format = models.CharField(
        max_length=10,
        choices=FORMAT_CHOICES,
        default='json',
        verbose_name="Format"
    )
    
    requested_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Talep Tarihi",
        db_index=True
    )
    
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="İşlenme Tarihi"
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Tamamlanma Tarihi"
    )
    
    # Export file paths
    json_file = models.FileField(
        upload_to='data_exports/json/',
        null=True,
        blank=True,
        verbose_name="JSON Dosyası"
    )
    
    csv_file = models.FileField(
        upload_to='data_exports/csv/',
        null=True,
        blank=True,
        verbose_name="CSV Dosyası"
    )
    
    # Download tracking
    downloaded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="İndirilme Tarihi"
    )
    
    download_count = models.IntegerField(
        default=0,
        verbose_name="İndirme Sayısı"
    )
    
    # Expiry (30 days after completion)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Geçerlilik Süresi"
    )
    
    # Error handling
    error_message = models.TextField(
        blank=True,
        verbose_name="Hata Mesajı"
    )
    
    # Metadata
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP Adresi"
    )
    
    user_agent = models.CharField(
        max_length=512,
        blank=True,
        verbose_name="User Agent"
    )
    
    class Meta:
        ordering = ['-requested_at']
        verbose_name = "Veri İhraç Talebi"
        verbose_name_plural = "Veri İhraç Talepleri"
        indexes = [
            models.Index(fields=['user', '-requested_at']),
            models.Index(fields=['status', '-requested_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.format} ({self.status})"
    
    def is_expired(self):
        """Check if export has expired."""
        if self.expires_at and timezone.now() > self.expires_at:
            return True
        return False
    
    def mark_downloaded(self):
        """Track download."""
        self.download_count += 1
        if not self.downloaded_at:
            self.downloaded_at = timezone.now()
        self.save()


class ConsentRecord(models.Model):
    """
    User consent tracking (KVKK/GDPR compliance).
    
    Tracks user consent for:
    - Data processing
    - Marketing communications
    - Third-party sharing
    - Analytics/cookies
    """
    
    CONSENT_TYPE_CHOICES = [
        ('data_processing', 'Veri İşleme'),
        ('marketing', 'Pazarlama İletişimi'),
        ('third_party', 'Üçüncü Taraf Paylaşımı'),
        ('analytics', 'Analitik/Çerezler'),
        ('terms', 'Kullanım Koşulları'),
        ('privacy_policy', 'Gizlilik Politikası'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='consents',
        verbose_name="Kullanıcı"
    )
    
    consent_type = models.CharField(
        max_length=50,
        choices=CONSENT_TYPE_CHOICES,
        verbose_name="İzin Türü",
        db_index=True
    )
    
    consented = models.BooleanField(
        default=False,
        verbose_name="İzin Verdi"
    )
    
    consented_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="İzin Tarihi",
        db_index=True
    )
    
    # Consent withdrawal
    withdrawn_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="İzin Geri Çekme Tarihi"
    )
    
    # Metadata
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP Adresi"
    )
    
    user_agent = models.CharField(
        max_length=512,
        blank=True,
        verbose_name="User Agent"
    )
    
    # Consent version (for policy updates)
    policy_version = models.CharField(
        max_length=20,
        default='1.0',
        verbose_name="Politika Versiyonu"
    )
    
    class Meta:
        ordering = ['-consented_at']
        verbose_name = "İzin Kaydı"
        verbose_name_plural = "İzin Kayıtları"
        indexes = [
            models.Index(fields=['user', 'consent_type', '-consented_at']),
        ]
        unique_together = ['user', 'consent_type', 'policy_version']
    
    def __str__(self):
        status = "✓" if self.consented else "✗"
        return f"{self.user.username} - {self.consent_type} {status}"
    
    def withdraw(self):
        """Withdraw consent."""
        self.consented = False
        self.withdrawn_at = timezone.now()
        self.save()


class AccountDeletionRequest(models.Model):
    """
    Account deletion requests (KVKK/GDPR Right to be Forgotten).
    
    Users can request complete account deletion.
    Implements:
    - Grace period (7 days to cancel)
    - Data anonymization (optional)
    - Complete deletion
    """
    
    STATUS_CHOICES = [
        ('pending', 'Beklemede'),
        ('grace_period', 'Bekleme Süresi'),
        ('processing', 'İşleniyor'),
        ('completed', 'Tamamlandı'),
        ('cancelled', 'İptal Edildi'),
    ]
    
    DELETION_TYPE_CHOICES = [
        ('full', 'Tam Silme'),
        ('anonymize', 'Anonimleştirme'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='deletion_requests',
        verbose_name="Kullanıcı"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Durum",
        db_index=True
    )
    
    deletion_type = models.CharField(
        max_length=20,
        choices=DELETION_TYPE_CHOICES,
        default='full',
        verbose_name="Silme Türü"
    )
    
    reason = models.TextField(
        blank=True,
        verbose_name="Sebep"
    )
    
    requested_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Talep Tarihi",
        db_index=True
    )
    
    # Grace period (7 days to cancel)
    grace_period_ends_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Bekleme Süresi Bitişi"
    )
    
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="İşlenme Tarihi"
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Tamamlanma Tarihi"
    )
    
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="İptal Tarihi"
    )
    
    # Metadata
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP Adresi"
    )
    
    # Data summary (what will be deleted)
    documents_count = models.IntegerField(
        default=0,
        verbose_name="Doküman Sayısı"
    )
    
    queries_count = models.IntegerField(
        default=0,
        verbose_name="Sorgu Sayısı"
    )
    
    exports_count = models.IntegerField(
        default=0,
        verbose_name="Export Sayısı"
    )
    
    class Meta:
        ordering = ['-requested_at']
        verbose_name = "Hesap Silme Talebi"
        verbose_name_plural = "Hesap Silme Talepleri"
        indexes = [
            models.Index(fields=['user', '-requested_at']),
            models.Index(fields=['status', '-requested_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.deletion_type} ({self.status})"
    
    def cancel(self):
        """Cancel deletion request."""
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.save()
    
    def is_in_grace_period(self):
        """Check if still in grace period."""
        if self.grace_period_ends_at and timezone.now() < self.grace_period_ends_at:
            return True
        return False


# ============================================================================
# CORPUS QUERY MODELS (Refactored for VRT/CoNLL-U Import)
# ============================================================================

class Sentence(models.Model):
    """Sentence within a document.
    
    Each sentence contains multiple tokens and maintains order within document.
    Supports both VRT and CoNLL-U formats.
    """
    
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='sentences',
        verbose_name="Belge"
    )
    
    index = models.IntegerField(
        verbose_name="Cümle Sırası",
        help_text="Belge içindeki sıra numarası (1'den başlar)"
    )
    
    text = models.TextField(
        verbose_name="Cümle Metni",
        help_text="Ham metin formu"
    )
    
    token_count = models.IntegerField(
        default=0,
        verbose_name="Token Sayısı"
    )
    
    # Metadata from VRT/CoNLL-U comments
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Metadata",
        help_text="Sentence-level metadata (sent_id, text, etc.)"
    )
    
    class Meta:
        verbose_name = "Cümle"
        verbose_name_plural = "Cümleler"
        ordering = ['document', 'index']
        indexes = [
            models.Index(fields=['document', 'index']),
        ]
    
    def __str__(self):
        preview = self.text[:50] + '...' if len(self.text) > 50 else self.text
        return f"Sentence {self.index} in {self.document.filename}: {preview}"


class Token(models.Model):
    """Linguistic token with full morphological annotations.
    
    Supports CoNLL-U 10-column format:
    ID, FORM, LEMMA, UPOS, XPOS, FEATS, HEAD, DEPREL, DEPS, MISC
    
    Also compatible with VRT format attributes.
    """
    
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='tokens',
        verbose_name="Belge"
    )
    
    sentence = models.ForeignKey(
        Sentence,
        on_delete=models.CASCADE,
        related_name='tokens',
        verbose_name="Cümle"
    )
    
    index = models.IntegerField(
        verbose_name="Token Sırası",
        help_text="Cümle içindeki pozisyon (1'den başlar)"
    )
    
    # Core token data
    form = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="Kelime Formu",
        help_text="Surface form (FORM in CoNLL-U)"
    )
    
    lemma = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        verbose_name="Lemma",
        help_text="Base form (LEMMA in CoNLL-U)"
    )
    
    upos = models.CharField(
        max_length=20,
        blank=True,
        db_index=True,
        verbose_name="UPOS",
        help_text="Universal POS tag (NOUN, VERB, etc.)"
    )
    
    xpos = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="XPOS",
        help_text="Language-specific POS tag"
    )
    
    feats = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Morph Features",
        help_text="Morphological features (Case=Nom|Number=Sing)"
    )
    
    # Dependency parsing
    head = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Head",
        help_text="Head token index (0 for root)"
    )
    
    deprel = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Dependency Relation",
        help_text="Syntactic relation to head (nsubj, obj, etc.)"
    )
    
    deps = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Enhanced Dependencies",
        help_text="Enhanced dependency graph"
    )
    
    misc = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Misc",
        help_text="Additional annotations (SpaceAfter=No, etc.)"
    )
    
    # VRT-specific fields (custom attributes)
    vrt_attributes = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="VRT Attributes",
        help_text="Extra VRT tab-separated attributes"
    )
    
    class Meta:
        verbose_name = "Token"
        verbose_name_plural = "Tokens"
        ordering = ['document', 'sentence', 'index']
        indexes = [
            models.Index(fields=['document', 'index']),
            models.Index(fields=['sentence', 'index']),
            models.Index(fields=['form']),  # Fast concordance lookup
            models.Index(fields=['lemma']),
            models.Index(fields=['upos']),
        ]
    
    def __str__(self):
        return f"{self.form} ({self.lemma}/{self.upos}) in Sent {self.sentence.index}"
    
    def to_conllu_line(self):
        """Export token as CoNLL-U format line."""
        return '\t'.join([
            str(self.index),
            self.form,
            self.lemma or '_',
            self.upos or '_',
            self.xpos or '_',
            self.feats or '_',
            str(self.head) if self.head is not None else '_',
            self.deprel or '_',
            self.deps or '_',
            self.misc or '_',
        ])


class CorpusMetadata(models.Model):
    """Document-level corpus metadata.
    
    Stores header information from VRT/CoNLL-U files that doesn't fit
    in standard Document fields.
    """
    
    document = models.OneToOneField(
        Document,
        on_delete=models.CASCADE,
        related_name='corpus_metadata',
        verbose_name="Belge"
    )
    
    FORMAT_CHOICES = [
        ('vrt', 'VRT (Corpus Workbench)'),
        ('conllu', 'CoNLL-U (Universal Dependencies)'),
        ('plain', 'Plain Text'),
    ]
    
    source_format = models.CharField(
        max_length=20,
        choices=FORMAT_CHOICES,
        verbose_name="Kaynak Format"
    )
    
    # Global metadata (from VRT <text> attributes or CoNLL-U # global comments)
    global_metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Global Metadata",
        help_text="Document-level attributes (author, date, genre, etc.)"
    )
    
    # Structural metadata (VRT <p>, <s> hierarchies)
    structural_annotations = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Yapısal Anotasyonlar",
        help_text="Paragraph, section, speaker information"
    )
    
    # Import tracking
    imported_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="İmport Tarihi"
    )
    
    imported_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="İmport Eden"
    )
    
    original_filename = models.CharField(
        max_length=500,
        verbose_name="Orijinal Dosya Adı"
    )
    
    file_hash = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="Dosya Hash (SHA256)",
        help_text="Duplicate detection"
    )
    
    # Statistics
    sentence_count = models.IntegerField(
        default=0,
        verbose_name="Cümle Sayısı"
    )
    
    unique_lemmas = models.IntegerField(
        default=0,
        verbose_name="Benzersiz Lemma Sayısı"
    )
    
    unique_forms = models.IntegerField(
        default=0,
        verbose_name="Benzersiz Form Sayısı"
    )
    
    class Meta:
        verbose_name = "Korpus Metadata"
        verbose_name_plural = "Korpus Metadata"
    
    def __str__(self):
        return f"Metadata for {self.document.filename} ({self.source_format})"

