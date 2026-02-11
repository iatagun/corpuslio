# CorpusIO Geliştirme Görevleri

## 🎯 Öncelik Sırası

### ✅ Tamamlanan
- [x] Kullanıcı kimlik doğrulama sistemi (login, register, logout, profile)
- [x] Rol tabanlı erişim kontrolü (Academician, Developer, Superuser)
- [x] Multi-theme sistemi (dark, light, auto)
- [x] Gelişmiş bildirim sistemi (icons, animations, auto-dismiss)
- [x] Platform adı değişikliği (OCRchestra → CorpusIO)
- [x] Türkçe dil desteği
- [x] API dokümantasyonu (DRF Spectacular)

---

## 📋 Öncelik 1: Temel UX İyileştirmeleri

### [x] 1. Loading Göstergeleri ✅ TAMAMLANDI
- [x] Dosya yükleme sırasında progress bar
- [x] Skeleton screens (kart yüklenirken)
- [x] Spinner/loading animasyonları
- [x] Global loading overlay (showLoading/hideLoading fonksiyonları)
- **Gerçek süre:** 1 saat

### [x] 2. Toast Notifications Sistemi ✅ TAMAMLANDI
- [x] Köşede beliren modern bildirimler
- [x] Success, error, warning, info tipleri
- [x] Auto-dismiss ve manuel kapatma
- [x] Stack/queue sistemi (max 3 toast)
- [x] Progress bar ile countdown
- [x] Convenience methods (toastSuccess, toastError, toastWarning, toastInfo)
- **Gerçek süre:** 1 saat

### [x] 3. Drag & Drop Dosya Yükleme ✅ TAMAMLANDI
- [x] Sürükle-bırak alanı (görsel geri bildirim ile)
- [x] Çoklu dosya seçimi
- [x] Dosya önizleme (tip bazlı Material Icons ile)
- [x] Dosya tipi validasyonu (PDF, DOCX, DOC, TXT, PNG, JPG/JPEG)
- [x] Dosya boyut kontrolü (50MB limit)
- [x] Toast bildirimleri entegrasyonu
- [x] DataTransfer API ile senkronizasyon
- **Gerçek süre:** 1.5 saat

### [x] 4. Global Arama (Ctrl+K) ✅ TAMAMLANDI
- [x] Klavye kısayolu (Ctrl+K veya Cmd+K)
- [x] Modern modal arama penceresi (backdrop blur)
- [x] Hızlı sonuç gösterimi (belgeler ve koleksiyonlar)
- [x] AJAX ile debounced search (300ms)
- [x] Klavye navigasyonu (↑↓ gezinme, Enter seçim, ESC kapatma)
- [x] Tip bazlı gruplama ve ikonlar
- [x] Boş durum ve loading states
- **Gerçek süre:** 2 saat

### [x] 5. Lazy Loading ✅ TAMAMLANDI
- [x] Infinite scroll (kütüphane sayfası)
- [x] AJAX ile sayfa yenilemeden yükleme (20 öğe/sayfa)
- [x] Intersection Observer API kullanımı
- [x] Loading indicator (spinner ve mesaj)
- [x] "Tüm dokümanlar yüklendi" son mesajı
- [x] Filter desteği (arama/tür/yazar/tarih)
- **Gerçek süre:** 1.5 saat

---

## 📊 Öncelik 2: Analiz & Görselleştirme

### [x] 6. Dashboard Grafikleri ✅ TAMAMLANDI
- [x] Chart.js 4.4.1 entegrasyonu (Plotly.js yerine)
- [x] Yükleme trendi grafiği (son 30 gün, line chart)
- [x] Format dağılımı (doughnut chart, yüzde gösterimi)
- [x] Kelime sayısı istatistikleri (horizontal bar chart, top 20)
- [x] POS etiket dağılımı (polar area chart)
- [x] İnteraktif hover/tooltip (formatlanmış veriler)
- [x] Tema-uyumlu renkler ve animasyonlar
- **Gerçek süre:** 2 saat

### [x] 7. Kelime Bulutu (Word Cloud) ✅ TAMAMLANDI
- [x] WordCloud2.js entegrasyonu (Plotly yerine canvas-based)
- [x] Kelime ve lemma frekanslarından bulut oluşturma
- [x] Frekans bazlı dinamik boyutlandırma
- [x] Tema-uyumlu renk paleti (8 renk, dark/light)
- [x] PNG export özelliği (Canvas.toDataURL)
- [x] İnteraktif hover ve click (tooltip + toast bildirimi)
- [x] Responsive tasarım ve auto-resize
- [x] İstatistik kartları (toplam/benzersiz kelime/kök)
- **Gerçek süre:** 1.5 saat

### [ ] 8. Karşılaştırmalı Analiz
- [ ] İki korpusu karşılaştırma arayüzü
- [ ] Ortak kelimeler
- [ ] Fark analizi
- [ ] Görselleştirme
- [ ] **Tahmini süre:** 5-6 saat

### [ ] 9. Gelişmiş Export Formatları
- [ ] PDF export (raporlar)
- [ ] Excel export (istatistikler)
- [ ] CSV export (ham veri)
- [ ] Custom template desteği
- [ ] **Tahmini süre:** 4-5 saat

---

## 🔍 Öncelik 3: Arama & Filtreleme

### [ ] 10. Tag Sistemi
- [ ] Belgelere tag ekleme/çıkarma
- [ ] Tag bazlı filtreleme
- [ ] Tag renkleri
- [ ] Popüler taglar widget'ı
- [ ] **Tahmini süre:** 3-4 saat

### [ ] 11. Gelişmiş Arama
- [ ] Fuzzy search (benzer kelimeler)
- [ ] Regex desteği
- [ ] Multi-field search
- [ ] Arama geçmişi
- [ ] **Tahmini süre:** 4-5 saat

### [ ] 12. Kaydedilmiş Filtreler
- [ ] Filtre profilleri kaydetme
- [ ] Hızlı uygulama
- [ ] Paylaşılabilir filtre linkleri
- [ ] **Tahmini süre:** 2-3 saat

---

## 👥 Öncelik 4: İşbirliği Özellikleri

### [ ] 13. Activity Feed
- [ ] Son aktiviteler listesi
- [ ] Kullanıcı bazlı filtreleme
- [ ] Zaman damgası
- [ ] **Tahmini süre:** 2-3 saat

### [ ] 14. Belge Paylaşımı
- [ ] Paylaşım linki oluşturma
- [ ] Public/private toggle
- [ ] Şifre koruması (opsiyonel)
- [ ] Görüntüleme istatistikleri
- [ ] **Tahmini süre:** 3-4 saat

### [ ] 15. Yorum/Not Sistemi
- [ ] Belgelere yorum ekleme
- [ ] Annotation markers
- [ ] Thread/reply sistemi
- [ ] **Tahmini süre:** 5-6 saat

---

## ⚡ Öncelik 5: Performans & Optimizasyon

### [ ] 16. Redis Önbellekleme
- [ ] Redis kurulumu
- [ ] Sık kullanılan sorguları cache'leme
- [ ] Cache invalidation stratejisi
- [ ] **Tahmini süre:** 3-4 saat

### [ ] 17. Database Optimizasyonu
- [ ] Query profiling
- [ ] Index optimizasyonu
- [ ] N+1 sorunlarını çözme
- [ ] Pagination iyileştirmeleri
- [ ] **Tahmini süre:** 2-3 saat

### [ ] 18. Static Dosya Optimizasyonu
- [ ] CSS/JS minification
- [ ] Image optimization
- [ ] Gzip compression
- [ ] Browser caching headers
- [ ] **Tahmini süre:** 2-3 saat

---

## 🔐 Öncelik 6: Güvenlik & Yönetim

### [ ] 19. API Key Yönetimi
- [ ] Kullanıcı API anahtarı oluşturma
- [ ] API key rotasyonu
- [ ] Rate limiting per key
- [ ] Usage statistics
- [ ] **Tahmini süre:** 3-4 saat

### [ ] 20. Audit Log
- [ ] Kullanıcı aktivite kayıtları
- [ ] Admin görüntüleme paneli
- [ ] Filtreleme/arama
- [ ] Export özelliği
- [ ] **Tahmini süre:** 3-4 saat

### [ ] 21. 2FA (Two-Factor Authentication)
- [ ] TOTP desteği
- [ ] QR kod oluşturma
- [ ] Backup codes
- [ ] SMS opsiyonu (gelecek)
- [ ] **Tahmini süre:** 4-5 saat

---

## 📱 Öncelik 7: Mobil & Responsive

### [ ] 22. Mobil Optimizasyon
- [ ] Touch-friendly UI elements
- [ ] Hamburger menü
- [ ] Swipe gestures
- [ ] Mobile navigation
- [ ] **Tahmini süre:** 4-5 saat

### [ ] 23. Responsive Tables
- [ ] Card view (mobilde)
- [ ] Horizontal scroll
- [ ] Column toggle
- [ ] **Tahmini süre:** 2-3 saat

### [ ] 24. PWA Desteği
- [ ] Service worker
- [ ] Offline mode
- [ ] Install prompt
- [ ] Push notifications
- [ ] **Tahmini süre:** 5-6 saat

---

## 🎨 Öncelik 8: Tema & Özelleştirme

### [ ] 25. Custom Tema Oluşturma
- [ ] Renk paletini düzenleme arayüzü
- [ ] Tema kaydetme/yükleme
- [ ] Tema önizleme
- [ ] Community themes
- [ ] **Tahmini süre:** 4-5 saat

### [ ] 26. Klavye Kısayolları
- [ ] Shortcuts menüsü (?)
- [ ] Customizable shortcuts
- [ ] Cheatsheet modal
- [ ] **Tahmini süre:** 2-3 saat

### [ ] 27. Onboarding Tour
- [ ] İlk giriş rehberi
- [ ] Step-by-step walkthrough
- [ ] Interactive tutorial
- [ ] Skip/restart seçenekleri
- [ ] **Tahmini süre:** 3-4 saat

---

## 🌐 Öncelik 9: Çok Dilli Destek

### [ ] 28. i18n Sistemi
- [ ] Django i18n entegrasyonu
- [ ] Türkçe/İngilizce toggle
- [ ] Translation dosyaları
- [ ] Language switcher UI
- [ ] **Tahmini süre:** 4-5 saat

---

## 📧 Öncelik 10: Bildirimler & Entegrasyonlar

### [ ] 29. Email Bildirimleri
- [ ] İşlem tamamlandı emails
- [ ] Haftalık özet
- [ ] Email templates
- [ ] Bildirim tercihleri
- [ ] **Tahmini süre:** 3-4 saat

### [ ] 30. Toplu İşlemler
- [ ] Çoklu seçim checkbox
- [ ] Toplu silme
- [ ] Toplu export
- [ ] Toplu tag ekleme
- [ ] **Tahmini süre:** 2-3 saat

---

## 📈 Toplam Tahmini Süre
**Minimum:** ~90 saat  
**Maksimum:** ~120 saat

## 🚀 Önerilen İlk 5 Görev (Quick Wins)
1. ✅ Loading Göstergeleri (2-3h) - Hemen göze çarpan iyileştirme
2. ✅ Toast Notifications (2-3h) - UX için kritik
3. ✅ Tag Sistemi (3-4h) - Kullanıcı değeri yüksek
4. ✅ Dashboard Grafikleri (4-6h) - Görsel etki büyük
5. ✅ Lazy Loading (2-3h) - Performans iyileştirmesi

---

## 🔐 Öncelik 11: Email Verification & Security Features ✅ TAMAMLANDI

> **Stratejik Hedef:** Production-grade authentication sistemi ile institutional deployment hazırlığı

**📊 Task Status:** 11/11 Tasks Completed (100%)
- ✅ Phase 1 Core: 8 tasks (11.1 - 11.8) - Email verification workflow
- ✅ Phase 2 Security: 3 tasks (11.9 - 11.11) - Login security + Rate limiting + CSRF protection

**🛡️ Implemented Security Features:**
- Email Verification: Token-based with 24h expiration
- Account Locking: 5 failed attempts → 30 min lockout
- Rate Limiting: IP/user-based limits on login, registration, email resend
- CSRF Protection: All POST forms + AJAX global setup
- XSS Prevention: Django auto-escaping + CSP headers
- Password Strength: Min 8 chars, uppercase, lowercase, digit, weak password filtering

**📁 Modified Files:**
- Models: `corpus/models.py` (Migration 0016)
- Views: `corpus/views.py` (8 functions updated/added)
- Utils: `corpus/utils.py` (NEW - 4 security functions)
- Templates: 2 new email templates + 2 new verification pages + base.html AJAX setup
- Settings: `settings.py`, `settings_prod.py` (email + rate limit config)
- URLs: `corpus/urls.py` (3 new routes)

---

### Phase 1: Email Verification Core (MVP)

#### [x] Task 11.1: Model Enhancements ✅ TAMAMLANDI
**Dosya:** `corpus/models.py` → UserProfile model
- [x] Backend changes:
  - [x] `email_verified` field ekle (BooleanField, default=False)
  - [x] `email_verification_token` field ekle (CharField, max_length=64, unique=True, null=True)
  - [x] `email_verification_sent_at` field ekle (DateTimeField, null=True)
  - [x] `email_token_expires_at` field ekle (DateTimeField, null=True)
- [x] Helper methods:
  - [x] `generate_verification_token()` method (UUID4 kullan)
  - [x] `is_email_token_valid()` method (24 saat expiration)
  - [x] `mark_email_verified()` method
- [x] Bonus: Login security fields eklendi:
  - [x] `failed_login_attempts` field ekle (IntegerField, default=0)
  - [x] `last_failed_login` field ekle (DateTimeField, null=True)
  - [x] `account_locked_until` field ekle (DateTimeField, null=True)
  - [x] `is_account_locked()` method
  - [x] `record_failed_login()` method
  - [x] `reset_failed_login_attempts()` method
- [x] Migration oluştur ve çalıştır
- **Gerçek süre:** 0.5 saat

#### [x] Task 11.2: Email Configuration ✅ TAMAMLANDI
**Dosya:** `corpuslio_django/settings.py`
- [x] Development environment:
  - [x] `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'`
  - [x] Test email gönderimi ✅ Başarılı
- [x] Production environment (settings_prod.py):
  - [x] SMTP settings (Gmail/SendGrid/AWS SES için hazır config)
  - [x] Environment variables: `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`
  - [x] `DEFAULT_FROM_EMAIL = 'CorpusLIO <noreply@corpuslio.com>'`
- [x] Email template settings:
  - [x] Template path ayarları (Django default kullanıyor)
  - [x] Subject prefix: `[CorpusLIO]`
  - [x] HTML + Plain text fallback desteği hazır
- **Gerçek süre:** 0.25 saat

#### [x] Task 11.3: Utility Functions ✅ TAMAMLANDI
**Yeni dosya:** `corpus/utils.py`
- [x] `send_verification_email(user, request)` function:
  - [x] Token generation (UserProfile metodunu kullanıyor)
  - [x] Verification URL oluşturma (absolute URL)
  - [x] HTML email template render
  - [x] Plain text fallback
  - [x] Email gönderimi (Django send_mail)
  - [x] Error handling (email failure durumunda log)
- [x] `verify_email_token(token)` function:
  - [x] Token validation (DB'de var mı?)
  - [x] Expiration kontrolü (24 saat)
  - [x] User activation (is_active=True)
  - [x] Token invalidation (one-time use)
  - [x] Already verified check
- [x] `check_password_strength(password)` function:
  - [x] Min 8 karakter
  - [x] En az 1 büyük harf
  - [x] En az 1 küçük harf
  - [x] En az 1 rakam
  - [x] Common weak password kontrolü
  - [x] Return: (is_valid: bool, errors: list)
- [x] Bonus: `get_password_strength_score(password)` - 0-100 arası güç puanı
- [x] Test edildi: Password validation ✅ Çalışıyor (12345→Fail, MyP@ssw0rd123→Pass)
- **Gerçek süre:** 0.5 saat

#### [x] Task 11.4: Email Templates ✅ TAMAMLANDI
**Yeni klasör:** `templates/emails/`
- [x] `verification_email.html` oluştur:
  - [x] Modern, responsive email template
  - [x] Branding (CorpusLIO logo/colors) - Gradient header
  - [x] Verification button (call-to-action)
  - [x] Token expiration uyarısı (24 saat) - Alert box
  - [x] Support link ve footer
  - [x] Alternative link section (security best practice)
  - [x] Mobile responsive (@media queries)
  - [x] Security note (beklenmeyen email uyarısı)
- [x] `verification_email.txt` oluştur:
  - [x] Plain text version (email clients without HTML)
  - [x] Verification link
  - [x] 24 saat expiration uyarısı
  - [x] Security notes
  - [x] Temiz, okunabilir format
- **Gerçek süre:** 0.5 saat

#### [x] Task 11.5: Registration View Updates ✅ TAMAMLANDI
**Dosya:** `corpus/views.py` → `register_view()`
- [x] Password strength validation:
  - [x] `check_password_strength()` ile validasyon
  - [x] Error messages (specific: "at least 1 uppercase", etc.)
  - [x] Her hata için ayrı message gösterilir
- [x] User creation changes:
  - [x] User oluştur ama `is_active=False` set et
  - [x] UserProfile otomatik oluşturuluyor (signal ile)
  - [x] Token generate et (send_verification_email içinde)
- [x] Email gönderimi:
  - [x] `send_verification_email()` çağır
  - [x] Success handling → verification_sent sayfasına redirect
  - [x] Failure handling → user sil, error mesajı göster
  - [x] Session'da email sakla (resend için)
- [x] Redirect changes:
  - [x] Login'e değil → `verification_sent` view'e redirect
- [x] Error messages improvement:
  - [x] Username exists: "👤 Bu kullanıcı adı zaten kullanılıyor."
  - [x] Email exists: "✉️ Bu email adresi zaten kayıtlı."
  - [x] Password weak: "🔑 [detaylı hata mesajları]"
  - [x] Email format validation
  - [x] Username format validation (alphanumeric + underscore)
- **Gerçek süre:** 0.5 saat

#### [x] Task 11.6: Email Verification Views ✅ TAMAMLANDI
**Dosya:** `corpus/views.py` (yeni views)
- [x] `email_verification_sent_view()`:
  - [x] "Email gönderildi" confirmation page
  - [x] Session'dan email oku
  - [x] Resend verification link hazırlığı
  - [x] Email yoksa register'a redirect
- [x] `email_verify_view(token)`:
  - [x] Token validation (`verify_email_token()`)
  - [x] User activation (`is_active=True`)
  - [x] Email verified flag (`email_verified=True`)
  - [x] Success message + redirect to login (template ile)
  - [x] Error handling: expired token, invalid token, already verified
  - [x] Session temizleme (pending_verification_email)
- [x] `resend_verification_view()`:
  - [x] Rate limiting (max 3/hour per user - `@ratelimit`)
  - [x] Yeni token generate
  - [x] Email yeniden gönder
  - [x] Success/error messages
  - [x] Already verified check
  - [x] User.DoesNotExist handling
- **Gerçek süre:** 0.5 saat

#### [x] Task 11.7: URL Patterns ✅ TAMAMLANDI
**Dosya:** `corpus/urls.py`
- [x] `path('auth/verification-sent/', views.email_verification_sent_view, name='verification_sent')`
- [x] `path('auth/verify-email/<str:token>/', views.email_verify_view, name='verify_email')`
- [x] `path('auth/resend-verification/', views.resend_verification_view, name='resend_verification')`
- **Gerçek süre:** 0.1 saat (Task 11.6 ile birlikte yapıldı)

#### [x] Task 11.8: Frontend Templates ✅ TAMAMLANDI
**Template updates:**
- [x] **Yeni:** `email_verification_sent.html`:
  - [x] "Check your email" modern UI
  - [x] Email icon/illustration (animated pulse)
  - [x] Resend button (60 second countdown - disabled first 60 seconds)
  - [x] Countdown timer (JavaScript)
  - [x] Spam folder check reminder
  - [x] Info box (troubleshooting tips)
  - [x] Rate limit friendly messages
  - [x] Responsive design (mobile-friendly)
- [x] **Yeni:** `email_verified.html`:
  - [x] Success state (green gradient, check icon)
  - [x] Error state (red gradient, error icon)
  - [x] Success animation (scale-in effect)
  - [x] "Email doğrulandı ✓" mesajı
  - [x] Login button
  - [x] Auto-redirect after 3 seconds (success durumunda)
  - [x] Error handling UI (expired, invalid, already verified)
  - [x] Conditional rendering (success/error)
- [x] Bonus: Password strength indicator planlandı (register.html için - future task)
- **Gerçek süre:** 1 saat

---

### Phase 2: Login Security Enhancements

#### [x] Task 11.9: Login View Security ✅ TAMAMLANDI
**Dosya:** `corpus/views.py` → `login_view()`
- [x] Email verification check:
  - [x] Login attempt'ta `user.profile.email_verified` kontrolü
  - [x] Verified değilse: error message + resend verification link
  - [x] Session'da email sakla (resend için)
- [x] Failed login tracking:
  - [x] UserProfile'da `record_failed_login()` method kullanımı
  - [x] Her başarısız login'de increment
  - [x] Başarılı login'de reset (`reset_failed_login_attempts()`)
- [x] Account locking:
  - [x] 5 başarısız denemeden sonra lock (30 dakika)
  - [x] `is_account_locked()` kontrolü
  - [x] Lock durumunda friendly error: "Çok fazla başarısız deneme. X dakika sonra tekrar deneyin."
  - [x] Lock timer countdown göster (remaining minutes)
  - [x] Kalan deneme hakkı warning (≤2 kaldığında)
- [x] Security logging:
  - [x] User.DoesNotExist handling (don't reveal if user exists)
  - [x] Failed login reason tracking
  - [x] Informative error messages (security-aware)
- **Gerçek süre:** 0.5 saat

#### [x] Task 11.10: Rate Limiting (django-ratelimit) ✅ TAMAMLANDI
**Package installation & configuration:**
- [x] `pip install django-ratelimit` (requirements.txt'te zaten var: `django-ratelimit==4.1.0`)
- [x] Registration rate limit:
  - [x] `@ratelimit(key='ip', rate='5/h')` - IP bazlı 5 kayıt/saat
  - [x] `@ratelimit(key='post:email', rate='3/d')` - Email bazlı 3 kayıt/gün
  - [x] Ratelimit aşılınca: "Çok fazla kayıt denemesi yaptınız. Lütfen bir süre bekleyip tekrar deneyin."
- [x] Login rate limit:
  - [x] `@ratelimit(key='ip', rate='20/m')` - IP bazlı 20 deneme/dakika
  - [x] `@ratelimit(key='post:username', rate='10/m')` - Username bazlı 10 deneme/dakika
- [x] Resend verification rate limit (already done in Task 11.6):
  - [x] `@ratelimit(key='user_or_ip', rate='3/h')` - 3 email/saat
- [x] Custom ratelimit handler (`ratelimit_handler` view):
  - [x] Path-based error detection (login/register/verification)
  - [x] Friendly error messages (Türkçe)
  - [x] HTTP 429 status code
  - [x] Template rendering per context
  - [x] Settings: `RATELIMIT_VIEW = 'corpus.views.ratelimit_handler'`
- **Gerçek süre:** 1 saat

#### [x] Task 11.11: CSRF & XSS Protection ✅ TAMAMLANDI
**Security hardening:**
- [x] CSRF token validation:
  - [x] Tüm POST forms'da `{% csrf_token %}` kontrolü ✅ (login.html, register.html, email_verification_sent.html)
  - [x] AJAX requests'te `X-CSRFToken` header ✅ (base.html'de global setup)
    - [x] jQuery AJAX setup: `$.ajaxSetup()` with beforeSend
    - [x] Fetch API wrapper: Auto-inject CSRF header for POST/PUT/DELETE
    - [x] getCookie() helper function
- [x] XSS prevention:
  - [x] Django templates auto-escaping active ✅ (DjangoTemplates backend, no overrides)
  - [x] User input sanitization ✅ (Django default escaping for {{ variables }})
  - [x] `Content-Security-Policy` header ✅ (security_middleware.py - CSP header configured)
    - [x] CSP-Report-Only mode in development
    - [x] Strict CSP in production
- [x] SQL Injection protection:
  - [x] Django ORM used everywhere ✅ (no raw SQL in production views)
  - [x] Raw SQL only in debug scripts (scripts/*.py - non-production code)
  - [x] All database queries parameterized via ORM
- **Gerçek süre:** 0.5 saat

---

### Phase 3: Advanced Features (Future)

#### [x] Task 11.12: Password Reset Flow ✅ TAMAMLANDI
**Dosya:** `corpus/models.py`, `corpus/views.py`, `corpus/utils.py`, `corpus/urls.py`, `templates/`
- [x] Model enhancements:
  - [x] `password_reset_token` field ekle (CharField, max_length=64, unique=True, null=True)
  - [x] `password_reset_sent_at` field ekle (DateTimeField, null=True)
  - [x] `password_reset_expires_at` field ekle (DateTimeField, null=True - 1 saat)
  - [x] `generate_password_reset_token()` method (UUID4, 1 saat expiration)
  - [x] `is_reset_token_valid()` method
  - [x] `clear_reset_token()` method
- [x] Migration oluştur ve çalıştır (Migration 0017)
- [x] Utility functions (`corpus/utils.py`):
  - [x] `send_password_reset_email(user, request)` - Email gönderimi
  - [x] `verify_password_reset_token(token)` - Token validation
- [x] Email templates:
  - [x] `password_reset_email.html` - Modern responsive email (pink/red gradient)
  - [x] `password_reset_email.txt` - Plain text fallback
- [x] Views (`corpus/views.py`):
  - [x] `password_reset_request_view()` - Email input form + rate limiting (5/h)
  - [x] `password_reset_sent_view()` - Confirmation page
  - [x] `password_reset_confirm_view(token)` - New password form + validation
- [x] URL patterns (`corpus/urls.py`):
  - [x] `/auth/password-reset/` → password_reset_request
  - [x] `/auth/password-reset-sent/` → password_reset_sent
  - [x] `/auth/reset/<token>/` → password_reset_confirm
- [x] Frontend templates (auth-page design):
  - [x] `password_reset_request.html` - Email input form
  - [x] `password_reset_sent.html` - Confirmation with security tips
  - [x] `password_reset_confirm.html` - New password form with strength meter
- [x] Login page integration:
  - [x] "Şifremi Unuttum" button linked to password reset
- **Gerçek süre:** 2 saat

#### [ ] Task 11.13: Two-Factor Authentication (2FA)
- [ ] TOTP (Google Authenticator)
- [ ] SMS verification (Twilio integration)
- [ ] Backup codes
- [ ] 2FA setup wizard
- **Tahmini süre:** 6-8 saat

#### [ ] Task 11.14: Social Authentication
- [ ] Google OAuth
- [ ] GitHub OAuth
- [ ] ORCID OAuth (academic)
- [ ] Account linking
- **Tahmini süre:** 4-5 saat

#### [ ] Task 11.15: Advanced Security
- [ ] Login history (IP, device, location)
- [ ] Suspicious activity alerts
- [ ] Device management (logout from all devices)
- [ ] Session management
- **Tahmini süre:** 5-6 saat

---

### 📊 Phase 1 Toplam Tahmini Süre
**Minimum:** ~13 saat  
**Maksimum:** ~17 saat

### 🎯 Implementation Sırası (Öncelik)
1. **Task 11.1** → Model changes (foundation)
2. **Task 11.2** → Email config (infrastructure)
3. **Task 11.3** → Util functions (core logic)
4. **Task 11.4** → Email templates (UX)
5. **Task 11.5** → Registration update (integration)
6. **Task 11.6** → Verification views (workflow)
7. **Task 11.7** → URL routing (accessibility)
8. **Task 11.8** → Frontend templates (user-facing)
9. **Task 11.9** → Login security (critical)
10. **Task 11.10** → Rate limiting (brute-force protection)
11. **Task 11.11** → CSRF/XSS (hardening)

### ✅ Definition of Done (Her Task İçin)
- [ ] Code yazıldı ve test edildi
- [ ] Migration çalıştırıldı (model değişiklikleri için)
- [ ] Error handling implement edildi
- [ ] User-friendly messages (Türkçe)
- [ ] Console'da test edildi (email backend için)
- [ ] Git commit (atomic commits, descriptive messages)

---

## �📝 Notlar
- Her görev tamamlandıkça `[x]` ile işaretlenecek
- Öncelikler kullanıcı geri bildirimine göre değiştirilebilir
- Test coverage her özellik için yazılmalı
- Documentation güncellenmeli
