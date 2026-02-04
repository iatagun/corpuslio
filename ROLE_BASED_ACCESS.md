# Rol Bazlı Görünüm ve Erişim Kontrolü

## 🎯 Eklenen Özellikler

### 1. View-Level Erişim Kontrolü

Tüm view'lara `@login_required` decorator eklendi:

#### Genel Erişim (Giriş Gerekli)
- ✅ Ana Sayfa (`home_view`) - Herkes erişebilir (giriş gerekmez)
- 🔒 Kütüphane (`library_view`) - Giriş gerekli
- 🔒 Analiz (`analysis_view`) - Giriş gerekli
- 🔒 İstatistikler (`statistics_view`) - Giriş gerekli
- 🔒 Dashboard (`dashboard_view`) - Giriş gerekli
- 🔒 Koleksiyonlar (`collections_view`) - Giriş gerekli
- 🔒 N-gram Analizi (`ngrams_view`) - Giriş gerekli
- 🔒 Wordcloud (`wordcloud_view`) - Giriş gerekli

#### Akademik Erişim (Academician/Developer/Admin)
- 👨‍🎓 Dosya Yükleme (`upload_view`) - Sadece akademisyenler
- 👨‍🎓 Koleksiyon Oluşturma (`create_collection_view`) - Sadece akademisyenler
- 👨‍🎓 Belge Silme (`delete_document`) - Sadece akademisyenler

### 2. Template-Level Rol Bazlı Görünüm

#### Ana Sayfa (home.html)
**Giriş Yapmamış Kullanıcılar:**
- ❌ İstatistikler gizli
- ❌ Son dokümanlar gizli
- ✅ "Giriş Yap" ve "Kayıt Ol" butonları
- ✅ Platform tanıtımı

**Giriş Yapmış Kullanıcılar:**
- ✅ İstatistikler görünür
- ✅ Son dokümanlar görünür
- ✅ Kütüphane erişimi
- ✅ Dashboard erişimi

**Akademisyenler:**
- ✅ Tüm özellikler
- ✅ "Analiz Başlat" butonu
- ✅ Yükleme sayfası erişimi

#### Sidebar (base.html)
**Giriş Yapmamış Kullanıcılar:**
- ✅ Ana Sayfa linki
- ✅ "Giriş Yap" butonu
- ❌ Diğer tüm menü öğeleri gizli

**Giriş Yapmış Kullanıcılar:**
- ✅ Ana Sayfa
- ✅ Kütüphane
- ✅ Koleksiyonlar
- ✅ Dashboard
- ✅ İstatistikler
- ✅ API Docs

**Akademisyenler (+ Developer + Admin):**
- ✅ Tüm özellikler
- ✅ "Yükle (Akademik)" menü öğesi

#### Kütüphane (library.html)
**Standart Kullanıcılar:**
- ✅ Belgeleri görüntüleme
- ✅ Analiz sayfasına erişim
- ✅ VRT export
- ❌ Silme butonu gizli

**Akademisyenler:**
- ✅ Tüm özellikler
- ✅ Silme butonu görünür

#### Koleksiyonlar (collections.html)
**Standart Kullanıcılar:**
- ✅ Koleksiyonları görüntüleme
- ❌ "Yeni Koleksiyon" butonu gizli

**Akademisyenler:**
- ✅ Tüm özellikler
- ✅ "Yeni Koleksiyon" butonu görünür

### 3. Kullanıcı Rolleri

#### 🔹 Misafir (Giriş Yapmamış)
- Ana sayfa erişimi
- Platform tanıtımı
- Kayıt olma/giriş yapma

#### 🔹 Standart Kullanıcı
- Belgeleri görüntüleme
- Analiz araçlarına erişim
- Dashboard kullanımı
- İstatistikleri görüntüleme
- Koleksiyonları görüntüleme

#### 🔹 Academician (Akademisyen)
- Standart kullanıcı + 
- Dosya yükleme
- Belge silme
- Koleksiyon oluşturma

#### 🔹 Developer (Geliştirici)
- Academician ile aynı yetkiler

#### 🔹 Superuser (Süper Kullanıcı)
- Tüm yetkilere sahip
- Admin paneli erişimi

## 📋 Kullanım Örnekleri

### Yeni Kullanıcı Ekleme
```python
# Django shell veya admin panelinde
from django.contrib.auth.models import User, Group

# Standart kullanıcı oluştur
user = User.objects.create_user('john', 'john@example.com', 'password123')

# Akademisyen yap
academician_group = Group.objects.get(name='Academician')
user.groups.add(academician_group)
```

### Template'de Rol Kontrolü
```django
{% load auth_extras %}

<!-- Sadece akademisyenler görebilir -->
{% if request.user|has_group:"Academician" or request.user.is_superuser %}
    <button>Yükle</button>
{% endif %}

<!-- Giriş yapmış herkes görebilir -->
{% if user.is_authenticated %}
    <a href="{% url 'corpus:library' %}">Kütüphane</a>
{% endif %}
```

### View'de Rol Kontrolü
```python
from django.contrib.auth.decorators import login_required, user_passes_test

# Sadece giriş gerekli
@login_required
def my_view(request):
    pass

# Akademisyen kontrolü
@login_required
@user_passes_test(is_academician)
def upload_view(request):
    pass
```

## 🔐 Güvenlik Özellikleri

1. **View-Level Koruma**: Tüm kritik view'lar decorator ile korunuyor
2. **Template-Level Gizleme**: UI'da yetkisiz öğeler gizleniyor
3. **URL Koruma**: Yetkisiz erişim denemelerinde login sayfasına yönlendirme
4. **Rol Bazlı Filtreleme**: Kullanıcı rolüne göre özelleştirilen içerik

## 🎨 Kullanıcı Deneyimi

- Misafir kullanıcılar platform tanıtımını görür
- Giriş yapmamış kullanıcılar sidebar'da "Giriş Yap" butonu görür
- Akademisyenler ek menü öğelerini görür
- Silme gitehlikli işlemler sadece yetkili kullanıcılara gösterilir
- Her kullanıcı sadece yetkisine uygun özellikleri görür

## 📊 Test Hesapları

**Admin Hesabı:**
- Kullanıcı Adı: `admin`
- Şifre: `admin123`
- Rol: Süper Kullanıcı (Tüm yetkiler)

**Test için Akademisyen Hesabı Oluşturma:**
```bash
cd ocrchestra_django
python manage.py shell
```
```python
from django.contrib.auth.models import User, Group
user = User.objects.create_user('akademisyen', 'akademisyen@test.com', 'test123')
group = Group.objects.get(name='Academician')
user.groups.add(group)
```
