CorpusLIO
=========

Kısa Açıklama
-------------
CorpusLIO, Türkçe korpus verisi yönetimi, arama ve analiz için geliştirilen bir platformdur. Bu depo, proje kodunu (backend, API ve yönetim arayüzü) içerir.

Hızlı Başlangıç (geliştirme)
----------------------------
1. Sanal ortam oluşturun ve bağımlılıkları yükleyin:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r corpuslio_django/requirements.txt
```

2. Ortam değişkenini ayarlayın (geliştirme ayarları):

```powershell
$env:DJANGO_SETTINGS_MODULE='corpuslio_django.settings'
```

3. Veri tabanını hazırlayın ve süper kullanıcı oluşturun:

```powershell
cd corpuslio_django
python manage.py migrate
python manage.py createsuperuser
```

4. Sunucuyu çalıştırın:

```powershell
python manage.py runserver
# API şeması: http://127.0.0.1:8000/tr/api/schema/
```

API Dökümantasyonu
------------------
Proje, DRF + drf-spectacular kullanarak OpenAPI (Swagger/Redoc) tanımı üretir. Yerel olarak `/tr/api/schema/` adresinden YAML/JSON schema alabilirsiniz; ayrıca proje üzerinde interaktif dokümantasyon eklenecekse `drf-spectacular` ile Swagger/Redoc sayfaları sunulabilir.

Üretim (PythonAnywhere vb.)
--------------------------
- Üretim için `corpuslio_django/corpuslio_django/settings_prod.py` ve `wsgi_prod.py` hazırlandı. Bu ayarlar `DATABASE_URL` gibi environment değişkenleriyle çalışır ve `whitenoise` desteği içerir.
- Collectstatic çalıştırın ve statik dosyaları sunucuya kopyalayın:

```powershell
$env:DJANGO_SETTINGS_MODULE='corpuslio_django.settings_prod'
python manage.py collectstatic --noinput
```

- PythonAnywhere gibi barındırma ortamlarında `wsgi_prod.py` kullanarak uygulamayı bağlayın.

Notlar
------
- Proje paketleri `corpuslio` ve `corpuslio_django` olarak yeniden adlandırıldı; tüm importlar güncellendi.
- API şeması üretimi ve import kontrolleri yerel ortamda test edildi.

Katkıda Bulunma
---------------
1. Fork'unuzu oluşturun.
2. Yeni bir branch açın.
3. Değişiklikleri yapın, test edin ve PR açın.

Lisans ve İletişim
-----------------
Bu proje [https://github.com/iatagun/corpuslio](https://github.com/iatagun/corpuslio) adresinde barındırılmaktadır.

