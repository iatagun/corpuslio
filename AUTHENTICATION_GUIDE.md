# Kullanıcı Girişi ve Profil Sistemi

## ✅ Eklenen Özellikler

### 1. Kullanıcı Girişi ve Kayıt
- **Giriş Sayfası**: `/login/` - Kullanıcılar sisteme giriş yapabilir
- **Kayıt Sayfası**: `/register/` - Yeni kullanıcılar hesap oluşturabilir
- **Çıkış**: Profil menüsünden çıkış yapabilme

### 2. Profil Yönetimi
- **Profil Sayfası**: `/profile/` - Kullanıcı bilgilerini görüntüleme
- **Dinamik Profil Dropdown**: Sağ üstte kullanıcı adı ve rolü görüntülenir
- **Dropdown Menü**:
  - Profil sayfasına gitme
  - Admin paneline erişim (admin kullanıcılar için)
  - Çıkış yapma

### 3. Yetkilendirme
- Giriş yapmamış kullanıcılar için "Giriş Yap" butonu
- Giriş yapmış kullanıcılar için profil dropdown menüsü
- Rol bazlı görünüm (Süper Kullanıcı, Academician, Developer, Standart Kullanıcı)

## 🔑 Test Hesabı

**Kullanıcı Adı**: `admin`  
**Şifre**: `admin123`

Bu süper kullanıcı hesabı ile tüm özelliklere erişebilirsiniz.

## 📝 Kullanım

1. Tarayıcınızı yenileyin: http://127.0.0.1:8000/
2. Sağ üstte "Giriş Yap" butonuna tıklayın
3. Kullanıcı adı ve şifre ile giriş yapın
4. Giriş yaptıktan sonra sağ üstte profiliniz görünecek
5. Profil resmine tıklayarak dropdown menüyü açabilirsiniz

## 🎨 Özellikler

- Modern ve profesyonel arayüz
- Responsive tasarım
- Animasyonlu dropdown menü
- Rol bazlı renkli etiketler
- Türkçe dil desteği
- Güvenli oturum yönetimi

## 📁 Oluşturulan Dosyalar

1. `templates/corpus/login.html` - Giriş sayfası
2. `templates/corpus/register.html` - Kayıt sayfası
3. `templates/corpus/profile.html` - Profil sayfası
4. `corpus/views.py` - Authentication view'ları eklendi
5. `corpus/urls.py` - Authentication URL'leri eklendi
6. `static/css/styles.css` - Profil dropdown stilleri eklendi
7. `templates/corpus/base.html` - Profil dropdown fonksiyonelliği eklendi

## 🔐 Güvenlik

- Şifre doğrulama (minimum 8 karakter)
- CSRF koruması
- Kullanıcı adı ve email uniqueness kontrolü
- Login required decorator ile korumalı sayfalar
- Güvenli şifre hashleme (Django varsayılan)
