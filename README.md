# CorpusLIO - Turkish Corpus Platform

Modern Django-based Turkish corpus platform with AI-powered linguistic analysis.

**⚠️ This project has been migrated from Streamlit to Django.**

## 🚀 Quick Start

```bash
cd ocrchestra_django
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env and add GROQ_API_KEY

# Database
python manage.py migrate

# Create admin user
````markdown
# CorpusLIO - Turkish Corpus Platform (Current status)

Bu repo: Django tabanlı Türkçe korpus platformu gelişimi için çalışma kopyasıdır. Aşağıda güncel durum ve önemli notlar yer alır (2026-02-10).

## Hızlı Başlangıç

```bash
cd ocrchestra_django
pip install -r requirements.txt

# Ortam
cp .env.example .env
# .env içindeki ayarları düzenleyin

# Veritabanı
python manage.py migrate

# Yönetici oluşturun
python manage.py createsuperuser

# Geliştirme sunucusu
python manage.py runserver
```

Adres: http://localhost:8000

## Önemli Güncellemeler (mevcut durum)
- UI upload butonu ve `upload` sayfası kaldırıldı — belge yükleme artık yalnızca Django admin veya `import_corpus` management command ile yapılmalıdır.
- Site varsayılan olarak **dark theme** olarak zorlandı; tema/language seçimleri arayüzden gizlendi.
- Parsers (CoNLL-U / VRT) ve import pipeline güncellendi — `Content` ve `Analysis` kayıtları oluşturuluyor.
- `reparse_document` ve `fix_missing_analysis` management command'leri eklendi; mevcut belgeler için backfill/reparse işlemleri mümkün.
- Frekans, kollokasyon ve arama CTA'ları iyileştirildi; `corpus statistics` sayfasına hızlı arama butonları eklendi.
- Export watermark ve meta verilerinde kullanıcıya gösterilen marka adı `CorpusLIO` olarak güncellendi.

## Yapılacaklar / Bilinmesi Gerekenler
- Tüm kullanıcıya görünen "OCRchestra" metinleri tam taranıp `CorpusLIO` olarak merkezileştirilmeli (henüz tamamlanmadı).
- Marka adını merkezi bir ayar (`settings.BRAND_NAME`) içine taşıma önerisi var.
- Tam test kümesi çalıştırılmalı; şu anda `test_export_service.py` gibi bazı testler başarılı şekilde çalıştırıldı ama tam test çalıştırılmadı.
- Değişiklikler commit/push edilmedi — isterseniz ben commit ve push yapabilirim.

## Kısa Notlar (teknik)
- Upload endpoint: silindi (URL/şablon/view kaldırıldı). Admin veya `python manage.py import_corpus <file>` ile içe aktarma yapınız.
- Yönetici tarafı import komutları Windows için geçici dosya oluşturma ve temizleme içerir.

## Teknoloji
- Backend: Django
- Async (opsiyonel): Celery + Redis
- NLP araçları: yerel parserlar ve harici analiz entegrasyonları

## Lisans
MIT

````
## 🛠️ Technology Stack
