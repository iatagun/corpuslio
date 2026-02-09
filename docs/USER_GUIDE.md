# OCRchestra Kullanıcı Kılavuzu

**Versiyon:** 1.0  
**Tarih:** Şubat 2026  
**Platform:** OCRchestra - Ulusal Türkçe Korpus Platformu

---

## 📚 İçindekiler

1. [Giriş](#giriş)
2. [Hızlı Başlangıç](#hızlı-başlangıç)
3. [Hesap ve Roller](#hesap-ve-roller)
4. [Korpus Keşfi](#korpus-keşfi)
5. [Arama ve Sorgulama](#arama-ve-sorgulama)
6. [Analiz Araçları](#analiz-araçları)
7. [Veri İhracı](#veri-ihracı)
8. [Koleksiyon Yönetimi](#koleksiyon-yönetimi)
9. [Gizlilik ve Güvenlik](#gizlilik-ve-güvenlik)
10. [SSS](#sss)

---

## Giriş

### Platform Hakkında

OCRchestra, Türkiye'nin ulusal dijital metin korpusunu keşfetmek, sorgulamak ve analiz etmek için geliştirilen akademik bir platformdur. Üniversiteler, araştırmacılar, dil bilimciler ve öğrenciler için ücretsiz erişim sağlar.

**Temel Özellikler:**
- 🔍 Gelişmiş korpus sorgulama (concordance, kollokasyon, frekans)
- 📊 İstatistiksel analiz araçları (TTR, n-gram, distribution)
- 📥 Atıf ile su damgalı export (CSV, JSON, Excel)
- 🔐 KVKK ve GDPR uyumlu veri koruma
- 🌐 REST API erişimi (Developer+ roller için)
- 🏷️ Etiket ve koleksiyon sistemi

### Hedef Kitle

**Kimler Kullanabilir?**
- 📖 **Öğrenciler:** Ödev, proje ve araştırmalar için temel korpus erişimi
- 🎓 **Araştırmacılar:** Yüksek lisans, doktora ve akademik yayınlar için detaylı analiz
- 👨‍🏫 **Öğretim Görevlileri:** Dil eğitimi ve korpus dilbilim dersleri için kaynak
- 💻 **NLP Geliştiricileri:** Dil modeli eğitimi ve doğal dil işleme projeleri
- 🔬 **Dil Bilimciler:** Morfoloji, sözdizimi, semantik ve diyakronik araştırmalar

---

## Hızlı Başlangıç

### 1. Kayıt Olmak

**Adımlar:**
1. Ana sayfada **"Üye Ol"** butonuna tıklayın
2. Kullanıcı adı, e-posta ve şifre girin
3. Kurum ve rolünüzü seçin (öğrenci/araştırmacı/akademisyen)
4. E-posta doğrulama linkine tıklayın

**İpucu:** `.edu.tr` akademik e-posta adresi kullanırsanız doğrulama süreci hızlanır.

### 2. İlk Aramak

**Basit Arama:**
```
1. Ana sayfada "Korpusu Keşfet" butonuna tıklayın
2. Arama kutusuna bir kelime yazın (örn: "bilim")
3. Enter tuşuna basın veya arama butonuna tıklayın
4. Sonuçları KWIC (Keyword in Context) formatında görüntüleyin
```

**Klavye Kısayolları:**
- `Ctrl+K` veya `Cmd+K`: Hızlı arama modalı
- `Tab`: Sonuçlar arasında gezinme
- `Enter`: Seçili sonucu detaylandırma

### 3. İlk Export

**CSV Export:**
```
1. Arama sonuçları sayfasında "Export" butonuna tıklayın
2. Format olarak "CSV" seçin
3. İhraç edilecek veri kategorilerini seçin
4. "Export Oluştur" butonuna tıklayın
5. Downloads sayfasından CSV dosyasını indirin
```

**Önemli:** Export'lar su damgası ve otomatik kaynak atıfı ile gelir. Akademik yayınlarda kullanıma hazırdır.

---

## Hesap ve Roller

### Rol Sistemi

OCRchestra 5 seviyeli rol sistemi kullanır:

#### 1. 🌐 Anonim (Anonymous)
- **Özellikler:** Temel arama, ilk 10 sonuç görüntüleme
- **Kota:** Günlük 50 arama
- **Sınırlamalar:** Export yok, istatistik yok

#### 2. 📚 Kayıtlı Kullanıcı (Registered)
- **Özellikler:** Tam arama sonuçları, temel istatistikler, CSV export
- **Kota:** Günlük 100 arama, aylık 5MB export
- **Sınırlamalar:** Belge yükleme yok, API yok

#### 3. 🎓 Doğrulanmış Araştırmacı (Verified Researcher)
- **Özellikler:** Belge yükleme, koleksiyon oluşturma, JSON export
- **Kota:** Günlük 500 arama, aylık 20MB export
- **Doğrulama:** Akademik e-posta + kurum kaydı

#### 4. 💻 Developer
- **Özellikler:** REST API erişimi, toplu export, Excel format
- **Kota:** Günlük 2000 arama, aylık 100MB export
- **Doğrulama:** Proje açıklaması + API key başvurusu

#### 5. 👑 Admin
- **Özellikler:** Tüm yönetim paneli, kullanıcı onayları, sistem ayarları
- **Kota:** Sınırsız
- **Doğrulama:** Platform yöneticileri tarafından atanır

### Rol Yükseltme

**Araştırmacı Olmak:**
```
1. Profil sayfasına gidin
2. "Doğrulama Başvurusu" bölümüne tıklayın
3. Akademik e-posta adresinizi girin (.edu.tr)
4. Kurum ve bölüm bilgilerini doldurun
5. ORCID ID ekleyin (varsa, hızlandırır)
6. "Başvur" butonuna tıklayın
7. 3-5 iş günü içinde e-posta ile sonuç alın
```

**Developer Olmak:**
```
1. developer@ocrchestra.tr adresine e-posta gönderin
2. Konuyu "API Erişim Başvurusu" olarak belirtin
3. E-postada şunları belirtin:
   - Adınız ve kurumunuz
   - Proje açıklaması (ne yapmak istiyorsunuz?)
   - Beklenen kullanım miktarı
   - Mevcut OCRchestra kullanıcı adınız
4. 5-7 iş günü içinde incelenir
```

---

## Korpus Keşfi

### Library (Kütüphane) Sayfası

**Görünüm Modları:**
- **Liste Görünümü:** Tablo formatında tüm belgeler
- **Kart Görünümü:** Görsel önizlemeli kart düzeni
- **Kompakt Görünüm:** Yoğun liste (daha fazla sonuç)

**Filtreleme:**
```
📁 Formata Göre:
   - PDF, DOCX, TXT, OCR

📅 Tarihe Göre:
   - Bugün, Bu hafta, Bu ay, Özel aralık

🏷️ Etikete Göre:
   - Edebiyat, Bilim, Hukuk, Gazete, vb.

👤 Kullanıcıya Göre:
   - Kendi belgelerim
   - Tüm kullanıcılar
```

**Sıralama:**
- ⬆️ En yeni
- ⬇️ En eski
- 📊 En popüler (en çok sorgulanan)
- 🔤 Alfabetik (A→Z, Z→A)
- 💾 Dosya boyutu (küçük→büyük, büyük→küçük)

### Belge Detayları

**Bir Belgeye Tıkladığınızda:**
```
📋 Temel Bilgiler:
   - Dosya adı, yüklenme tarihi
   - Format, boyut, sayfa sayısı
   - Yükleyen kullanıcı

📊 İstatistikler:
   - Toplam kelime sayısı (token)
   - Benzersiz kelime sayısı (type)
   - Type-Token Ratio (TTR)
   - En sık kullanılan 10 kelime

🏷️ Etiketler:
   - Belge kategorileri
   - Konu başlıkları

🔍 Hızlı Eylemler:
   - Bu belgede ara
   - İstatistik analizi
   - Export bölümü
   - Koleksiyona ekle
```

---

## Arama ve Sorgulama

### Basit Arama

**Kelime Arama:**
```
Arama kutusu: "dilbilim"
Sonuç: Tüm "dilbilim" kelime eşleşmeleri KWIC formatında
```

**Özellikler:**
- Otomatik küçük/büyük harf duyarsızlık
- Türkçe karakterlere tam destek (ş, ğ, ı, ö, ü, ç)
- Anlık öneri (autocomplete)

### Gelişmiş Arama

#### 1. Regex (Düzenli İfadeler)

**Örnekler:**
```regex
# Herhangi bir -bilim ile biten kelime
.*bilim

# dil veya dili veya dile
dil[ie]?

# 5 harfli kelimeler (hepsi)
^.{5}$

# Sayı içeren kelimeler
.*\d+.*
```

**Aktive Etme:**
Arama kutusunun yanındaki "Regex" checkbox'ını işaretleyin.

#### 2. Fuzzy Search (Benzer Kelimeler)

**Kullanım:**
```
Arama: "oklama" (yanlış yazılım)
Fuzzy aktif → "okuma" sonuçlarını da gösterir

Arama: "bilgasayar" 
Fuzzy aktif → "bilgisayar" sonuçlarını da gösterir
```

**Aktive Etme:**
"Fuzzy" checkbox'ı işaretleyin. Distance: 1-2 karakterlik fark.

#### 3. Kollokasyon (Collocation)

**Tanım:** Bir kelimenin yakın çevresinde hangi kelimeler kullanıyor?

**Örnek:**
```
Kelime: "kahve"
Kollokasyonlar (±5 kelime pencere):
   - türk kahvesi (37 kez)
   - kahve içmek (28 kez)
   - kahve fincanı (19 kez)
   - kahve molası (14 kez)
```

**Kullanım:**
```
1. Analysis sayfasına gidin
2. "Collocation" sekmesine tıklayın
3. Kelime girin ve pencere boyutu seçin (±3, ±5, ±10)
4. "Analiz Et" butonuna tıklayın
```

#### 4. N-gram Analizi

**Tanım:** Ardışık n kelimelik dizilerin frekans analizi.

**Örnekler:**
```
Bigram (2-gram):
   "bu nedenle" → 145 kez
   "diğer taraftan" → 98 kez

Trigram (3-gram):
   "bu çalışmada ise" → 67 kez
   "öte yandan aynı" → 43 kez
```

**Kullanım:**
```
1. Analysis → "N-gram" sekmesi
2. N değerini seçin (2, 3, 4, 5)
3. Minimum frekans filtresi (örn: en az 10 kez)
4. "Hesapla" butonuna tıklayın
```

---

## Analiz Araçları

### 1. Frekans Analizi

**Kelime Sıklığı:**
```
Top 10:
1. ve       → 12,543 kez
2. bir      → 8,721 kez
3. bu       → 6,912 kez
4. için     → 5,334 kez
5. ile      → 4,987 kez
...
```

**Görselleştirme:**
- 📊 Bar chart (막대 grafik)
- 🥧 Pie chart (pasta grafik)
- ☁️ Word cloud (kelime bulutu)

**Export:** CSV, PNG, SVG formatlarında indirebilirsiniz.

### 2. Type-Token Ratio (TTR)

**Formül:**
```
TTR = Benzersiz Kelime Sayısı / Toplam Kelime Sayısı
```

**Yorumlama:**
```
TTR < 0.4   → Düşük kelime çeşitliliği (tekrarlı)
TTR 0.4-0.6 → Orta düzey çeşitlilik
TTR > 0.6   → Yüksek kelime çeşitliliği (zengin)
```

**Örnek Kullanım:**
İki yazarın kelime zenginliğini karşılaştırmak için TTR değerlerini inceleyin.

### 3. Konkordans (KWIC)

**Keyword in Context:**
```
[ Sol Bağlam ]      ANAHTAR      [ Sağ Bağlam ]
----------------------------------------------------
Türk dili ve     | DİLBİLİM |   alanında önemli
modern            | dilbilim |   teorileri inceler
uygulamalı        | dilbilim |   çalışmaları için
```

**Özelleştir:**
- Bağlam penceresi: 5-50 kelime
- Sıralama: Alfabetik, frekans, sol/sağ bağlam
- Vurgulama: Renkli işaretleme
- Filtreleme: POS tag, lematizasyon (gelecek özellik)

### 4. Distribution (Dağılım) Analizi

**Kullanım:**
Bir kelimenin korpus boyunca nasıl dağıldığını görselleştirin.

**Örnek:**
```
Kelime: "bilim"
Grafik: Zaman içinde kullanım eğilimi
   - 1990'lar: ▃▃▃▅▅
   - 2000'ler: ▅▅▇▇█
   - 2010'lar: ███▇▅
   - 2020'ler: ▇▅▅▃▃
```

**Yorumlama:**
2000'lerde "bilim" kelimesinin kullanımı zirve yapmış.

---

## Veri İhracı

### Export Formatları

#### 1. CSV (Comma-Separated Values)
**Kullanım Alanı:** Excel, R, Python pandas ile analiz

**İçerik:**
```csv
context_left,keyword,context_right,document,position
"Türk dili ve","dilbilim","alanında önemli","doc1.pdf",245
"modern","dilbilim","teorileri inceler","doc2.pdf",1203
```

**Su Damgası:**
Dosya başında yorum satırı olarak:
```csv
# OCRchestra - Ulusal Türkçe Korpus Platformu
# Export Tarihi: 2026-02-09
# Kullanıcı: researcher123
# Sorgu: "dilbilim"
# Atıf: OCRchestra Platformu. (2026). Ulusal Türkçe Korpus Veri Tabanı...
```

#### 2. JSON (JavaScript Object Notation)
**Kullanım Alanı:** API entegrasyonları, web uygulamaları

**İçerik:**
```json
{
  "metadata": {
    "platform": "OCRchestra",
    "export_date": "2026-02-09T14:30:00Z",
    "user": "researcher123",
    "query": "dilbilim",
    "citation": "OCRchestra Platformu. (2026)..."
  },
  "results": [
    {
      "left_context": "Türk dili ve",
      "keyword": "dilbilim",
      "right_context": "alanında önemli",
      "document": "doc1.pdf",
      "position": 245
    }
  ]
}
```

#### 3. Excel (.xlsx)
**Kullanım Alanı:** Akademik tablolar, sunum hazırlama

**Özellikler:**
- 3 sayfa: Results, Statistics, Citation
- Otomatik formatlanmış tablolar
- Grafik önizlemeleri
- Formüller (ortalama, standart sapma)

**Gereksinim:** Developer role veya üzeri

### Export Kotaları

| Rol                 | Günlük Export | Aylık Toplam | Max Dosya |
|---------------------|---------------|--------------|-----------|
| Registered          | 3             | 5 MB         | 1 MB      |
| Verified Researcher | 10            | 20 MB        | 5 MB      |
| Developer           | 50            | 100 MB       | 20 MB     |
| Admin               | ∞             | ∞            | ∞         |

**Kota Sıfırlama:**
- Günlük: Her gün 00:00 (UTC+3)
- Aylık: Her ayın 1'i 00:00 (UTC+3)

### Export İşlemi

**Adımlar:**
```
1. Arama sonuçları sayfasında "Export" butonuna tıklayın
2. Format seçin (CSV / JSON / Excel)
3. Veri kategorilerini seçin:
   [ ] KWIC sonuçları
   [ ] Frekans istatistikleri
   [ ] N-gram analizi
   [ ] Kollokasyonlar
4. Onaylayın ve "Export Oluştur" butonuna basın
5. İşlem tamamlandığında Dashboard → Downloads'a gidin
6. Export dosyasını indirin
```

**Süre:**
- Küçük export (<1000 satır): 5-10 saniye
- Orta export (1000-10000 satır): 30-60 saniye
- Büyük export (>10000 satır): 2-5 dakika

**Not:** Büyük export'lar arka planda işlenir ve hazır olunca e-posta bildirimi gelir.

---

## Koleksiyon Yönetimi

### Koleksiyon Nedir?

**Tanım:** Belirttiğiniz kriterlere göre belge grupları oluşturma. Kendi "alt-korpusunuz" olarak düşünün.

**Kullanım Senaryoları:**
- 📰 Tüm gazete haberlerini bir koleksiyonda toplama
- 📚 19. yüzyıl edebiyat eserlerini gruplandırma
- ⚖️ Hukuk metinlerini ayrı bir korpus yapma
- 🎓 Kendi tez çalışmanız için özel veri seti

### Koleksiyon Oluşturma

**Adımlar:**
```
1. Dashboard → "Collections" sekmesine gidin
2. "Yeni Koleksiyon" butonuna tıklayın
3. Bilgileri doldurun:
   - İsim: "19. Yüzyıl Türk Romanları"
   - Açıklama: "1850-1900 arası yazılmış romanlar"
   - Görünürlük: Özel / Paylaşımlı / Halka Açık
4. Belgeler ekleyin:
   - Manuel seçim (checkbox ile)
   - Toplu filtre (tag, tarih, kullanıcı)
5. "Oluştur" butonuna tıklayın
```

### Koleksiyon Özellikleri

**Görünürlük Seviyeleri:**
```
🔒 Özel (Private):
   - Sadece siz görebilirsiniz
   - Başkaları erişemez

👥 Paylaşımlı (Shared):
   - Belirttiğiniz kullanıcılarla paylaşılır
   - E-posta ile davet gönderme

🌐 Halka Açık (Public):
   - Tüm kullanıcılar görebilir
   - Arama sonuçlarında listelenir
   - Katkı sahibi siz olarak görünür
```

**İstatistikler:**
- Koleksiyondaki belge sayısı
- Toplam kelime sayısı
- Type-Token Ratio (TTR)
- En sık kelimeler (top 20)
- Oluşturma ve son güncelleme tarihi

### Koleksiyon Üzerinde Sorgulama

**Namespace Arama:**
```
Tüm korpusta ara → "collection:all dilbilim"
Sadece bir koleksiyonda ara → "collection:my-romans dilbilim"
```

**Export:**
Koleksiyon export'ları su damgasında koleksiyon bilgisini de içerir:
```
# Koleksiyon: 19. Yüzyıl Türk Romanları
# Belge Sayısı: 47
# Oluşturan: researcher123
```

---

## Gizlilik ve Güvenlik

### KVKK ve GDPR Uyumu

OCRchestra, Türkiye'nin **KVKK (6698 sayılı Kanun)** ve Avrupa'nın **GDPR** düzenlemelerine tam uyumlu çalışır.

**Haklarınız:**
- ✅ Erişim Hakkı: Verilerinizi görüntüleme
- ✅ Taşınabilirlik Hakkı: Verilerinizi JSON/CSV export
- ✅ Düzeltme Hakkı: Profil bilgilerinizi güncelleme
- ✅ Silme Hakkı ("Unutulma Hakkı"): Hesap silme
- ✅ İtiraz Hakkı: Veri işlemeye itiraz etme
- ✅ İzin Çekme Hakkı: Consent'leri geri çekme

### Veri İşleme

**Hangi Verileriniz İşlenir:**
```
Kimlik & İletişim:
   - Kullanıcı adı, e-posta
   - Kurum ve bölüm (opsiyonel)

Akademik & Profesyonel:
   - ORCID ID (opsiyonel)
   - Araştırma alanı (opsiyonel)

İşlem Güvenliği:
   - IP adresi (güvenlik, spam önleme)
   - Çerezler (oturum yönetimi)
   - Cihaz bilgisi (browser, işletim sistemi)

Platform Kullanımı:
   - Yüklenen belgeler
   - Arama sorguları (anonim istatistik)
   - Export geçmişi
```

**Veri Saklama Süreleri:**
```
Hesap Bilgileri → Hesap aktif olduğu sürece
Arama Logları → 2 yıl (aktif) + 1 yıl (pasif)
Export Dosyaları → 30 gün
Silme Talepleri → 7 gün (iptal penceresi)
```

### Consent (İzin) Yönetimi

**Erişim:**
Profil → Privacy Settings → Consent Management

**İzin Türleri:**
```
✅ Veri İşleme (Zorunlu):
   - Platform çalışması için gerekli
   - Çekilemez (hesap silinmeli)

◻️ Pazarlama İletişimi (Opsiyonel):
   - Platform güncellemeleri, bülten
   - İstediğiniz zaman kapat/aç

◻️ 3. Taraf Paylaşımı (Opsiyonel):
   - Anonim araştırma ortaklıkları
   - İstatistiksel veri paylaşımı

◻️ Analitik Çerezler (Opsiyonel):
   - Kullanım istatistikleri
   - Platform iyileştirme verileri
```

**İzin Geçmişi:**
Tüm consent değişiklikleriniz tarihleri ile kaydedilir ve görüntüleyebilirsiniz.

### Hesap Silme

**İşlem:**
```
1. Profil → Privacy Settings → "Hesabımı Sil"
2. Silme türü seçin:
   [ ] Tam silme (önerilir) → Tüm veriler silinir
   [ ] Anonimleştirme → Belgeler kalır, kimlik silinir
3. Kullanıcı adınızı doğrulayın
4. "Sil" butonuna tıklayın
5. 7 gün iptal penceresi başlar
```

**İptal Penceresi:**
- 7 gün içinde giriş yaparsanız silme iptal edilir
- "Cancel Deletion" butonu Dashboard'da görünür
- 7 gün sonra otomatik işleme başlar

**Silme Süresi:**
- Küçük hesaplar (<100 belge): Anında
- Orta hesaplar (100-1000 belge): 1-3 saat
- Büyük hesaplar (>1000 belge): 24-48 saat

**Ne Silinir:**
```
Tam Silme:
   - Hesap bilgileri
   - Profil verileri
   - Tüm yüklediğiniz belgeler
   - Oluşturduğunuz koleksiyonlar
   - Export geçmişi
   - Consent kayıtları

Anonimleştirme:
   - Hesap bağlantısı kesilir
   - Belgeler anonim kullanıcıya atanır
   - Araştırma bütünlüğü korunur
```

### Güvenlik Önlemleri

**Teknik:**
- 🔐 SSL/TLS şifrelemeli iletişim
- 🔒 Argon2 şifre hashleme
- 🛡️ Firewall ve DDoS koruması
- 🔄 Otomatik yedeklemeler (günlük)
- 📝 Detaylı audit logları

**İdari:**
- 👤 Rol tabanlı erişim kontrolü
- 🔍 Düzenli güvenlik denetimleri
- 📚 Personel eğitimi
- 🚨 Veri ihlali müdahale planı

**Kullanıcı Sorumlulukları:**
- Güçlü şifre kullanın (min. 8 karakter, büyük/küçük/sayı/özel karakter)
- 2FA (Two-Factor Authentication) aktive edin (yakında)
- Şüpheli aktivite durumunda bildirin: security@ocrchestra.tr

---

## SSS

### Genel Sorular

**S: Platform tamamen ücretsiz mi?**
C: Evet, eğitim ve araştırma amaçlı kullanım tamamen ücretsizdir. Ticari kullanım için lisans gereklidir.

**S: Hangi dilleri destekliyorsunuz?**
C: Şu anda sadece Türkçe korpus bulunuyor. Gelecekte çok dilli destek planlanıyor.

**S: Kaç belge var korpusta?**
C: Anlık istatistikler ana sayfada görüntülenir. Şubat 2026 itibarıyla ~10,000 belge ve ~50M token.

### Rol ve Kota Soruları

**S: Araştırmacı rolü başvurum ne kadar sürer?**
C: Akademik e-posta doğrulandıktan sonra 3-5 iş günü. ORCID ID eklerseniz daha hızlı işlenir.

**S: Export kotam doldu, ne yapmalıyım?**
C: Günlük kota ertesi gün sıfırlanır. Acil ihtiyaç için support@ocrchestra.tr'den artırım talep edebilirsiniz (gerekçe ile).

**S: Developer API key nasıl alırım?**
C: developer@ocrchestra.tr'ye proje detayları ile başvurun. İnceleme süresi 5-7 iş günü.

### Teknik Sorular

**S: Regex arama nasıl çalışır?**
C: Python `re` modülü kullanılır. Syntax: [Python Regex Docs](https://docs.python.org/3/library/re.html)

**S: Export dosyalarım ne kadar saklanır?**
C: 30 gün. Süre dolunca otomatik silinir. İndirmeyi unutmayın.

**S: API rate limit nedir?**
C: Developer: 100 request/dakika, 2000 request/gün. Admin: sınırsız.

### Gizlilik Soruları

**S: Aramalarım kaydediliyor mu?**
C: Evet, anonim istatistik için sorguları saklarız ama kullanıcı kimliği ile ilişkilendirmeyiz. Detay: Privacy Policy.

**S: Yüklediğim belgeler herkese açık mı?**
C: Hayır, varsayılan olarak özeldir. Paylaşım seviyesini koleksiyon ayarlarından değiştirebilirsiniz.

**S: KVKK talebi nasıl yaparım?**
C: Profil → Privacy Settings → ilgili bölüm. Veya kvkk@ocrchestra.tr'ye yazılı başvuru.

### Sorun Giderme

**S: Giriş yapamıyorum, şifremi unuttum.**
C: Giriş sayfasında "Şifremi Unuttum" linkine tıklayın. E-posta sıfırlama linki gelir.

**S: Export oluşturamıyorum, hata veriyor.**
C: Kotanızı kontrol edin (Dashboard → Usage). Hala sorun varsa support@ocrchestra.tr

**S: Arama sonuç vermiyor ama kelimenin olduğunu biliyorum.**
C: Türkçe karakterlere dikkat edin (i/ı, o/ö). Fuzzy search'ü aktive edin veya regex kullanın.

**S: Yüklemek istediğim belge format hatası veriyor.**
C: Desteklenen formatlar: PDF, DOCX, TXT. Max boyut: 50MB. OCR için PDF/PNG/JPG kabul edilir.

---

## İletişim ve Destek

### Destek Kanalları

**📧 E-posta:**
- Genel Sorular: support@ocrchestra.tr
- Teknik Sorunlar: tech@ocrchestra.tr
- Güvenlik: security@ocrchestra.tr
- Gizlilik/KVKK: privacy@ocrchestra.tr
- Developer/API: developer@ocrchestra.tr

**📱 Sosyal Medya:**
- Twitter: @ocrchestra_tr
- GitHub: github.com/ocrchestra
- Discussions: GitHub Discussions (topluluk desteği)

**📚 Dokümantasyon:**
- Kullanıcı Kılavuzu: `/docs/USER_GUIDE.md` (bu dosya)
- API Dokümantasyonu: `/docs/API_GUIDE.md`
- Arama Kılavuzu: `/docs/SEARCH_GUIDE.md`
- Export Kılavuzu: `/docs/EXPORT_GUIDE.md`

### Katkıda Bulunma

Platform açık kaynak ruhuyla geliştirilmektedir:

**Kod Katkısı:**
GitHub: [github.com/ocrchestra/platform](https://github.com/ocrchestra/platform) (örnek)

**Belge Bağışı:**
Kendi metin koleksiyonunuzu paylaşmak için: upload@ocrchestra.tr

**Çeviri:**
Arayüz İngilizce çevirisi için volunteers@ocrchestra.tr

**Hata Bildirimi:**
GitHub Issues veya tech@ocrchestra.tr

---

## Ek Kaynaklar

### Videolar (Yakında)

- ▶️ **Hızlı Başlangıç** (5 dakika): İlk arama ve export
- ▶️ **Gelişmiş Sorgulama** (15 dakika): Regex, kollokasyon, n-gram
- ▶️ **Koleksiyon Yönetimi** (10 dakika): Alt-korpus oluşturma
- ▶️ **API Kullanımı** (20 dakika): REST API ile entegrasyon

### Harici Araçlar

**Korpus Analizi:**
- AntConc: Masaüstü korpus analiz programı
- Sketch Engine: Web tabanlı korpus platformu
- Voyant Tools: Text analiz ve görselleştirme

**Python Kütüphaneleri:**
```python
import nltk          # Natural Language Toolkit
import spacy         # NLP pipeline
import pandas as pd  # Veri analizi
import matplotlib    # Görselleştirme
```

### Akademik Atıf

**APA 7 Format:**
```
OCRchestra Platformu. (2026). Ulusal Türkçe Korpus Veri Tabanı. 
Erişim tarihi: [GÜN ARALIK YIL]. https://ocrchestra.tr
```

**MLA Format:**
```
"OCRchestra Platformu." Ulusal Türkçe Korpus Veri Tabanı, 2026, 
www.ocrchestra.tr. Erişim [Gün Ay Yıl].
```

**Chicago Format:**
```
OCRchestra Platformu. "Ulusal Türkçe Korpus Veri Tabanı." 2026. 
https://ocrchestra.tr.
```

---

**Versiyon Geçmişi:**
- v1.0 (Şubat 2026): İlk yayın

**Son Güncelleme:** 9 Şubat 2026  
**Lisans:** [Creative Commons BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)

---

**OCRchestra - Ulusal Türkçe Korpus Platformu**  
*Eğitim ve Araştırma İçin Ücretsiz Erişim* 🇹🇷
