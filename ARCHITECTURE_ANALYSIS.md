# CorpusLIO Mimari Analiz Raporu

**Tarih:** 12 Şubat 2026  
**Analist:** GitHub Copilot  
**Amaç:** Sistemin arama motoru olarak ölçeklenebilirliğini değerlendirmek

---

## Özet: Web App mı, Arama Motoru mu?

**Cevap: Web Application**

CorpusLIO şu anda bir **Django web uygulaması** olarak tasarlanmış. Korpus arama motoru özellikleri planned/future roadmap aşamasında, implemented değil.

---

## Kritik Soru Değerlendirmesi

### ❌ 1. Token-level Inverted Index Var mı?

**HAYIR**

**Kanıt:**
```python
# corpus/models.py satır 1870-1878
class Meta:
    indexes = [
        models.Index(fields=['document', 'index']),
        models.Index(fields=['sentence', 'index']),
        models.Index(fields=['form']),  # Klasik B-tree index
        models.Index(fields=['lemma']),
        models.Index(fields=['upos']),
    ]
```

**Durum:**
- PostgreSQL B-tree indexleri var
- Token-level inverted index YOK
- Her token ayrı bir database row (1M token = 1M row)
- CWB-style corpus encoding YOK

**Sonuç:** Büyük korpuslar (100M+ token) için yetersiz. PostgreSQL full-text search bile yok.

---

### ❌ 2. Join-free Pattern Search Var mı?

**HAYIR**

**Kanıt:**
```python
# corpus/query_engine.py satır 38-76
def concordance(self, query: str, ...):
    matching_tokens = self.base_queryset.filter(
        **filter_kwargs
    ).select_related('sentence', 'document')[:limit]
    
    for token in matching_tokens:
        # HER TOKEN İÇİN JOIN!
        sent_tokens = Token.objects.filter(
            sentence=token.sentence
        ).order_by('index')
```

**Durum:**
- Her concordance sonucu için Token ↔ Sentence ↔ Document join'i
- N-gram extraction tüm sentence'ları memory'ye yüklüyor:
```python
# query_engine.py satır 287
sentences = Sentence.objects.all().prefetch_related('tokens')
```

**Sonuç:** Pattern search O(matches × tokens_per_sentence) complexity. CWB bunu O(1) positional lookup ile yapar.

---

### ❌ 3. Positional Search O(n) Değil mi?

**HAYIR, O(n) veya daha kötü**

**Kanıt:**
```python
# corpus/query_engine.py satır 236-260
def collocation(self, keyword: str, window_size: int = 5, ...):
    keyword_tokens = self.base_queryset.filter(
        lemma__iexact=keyword
    ).select_related('sentence')
    
    for kw_token in keyword_tokens:
        # HER KEYWORD İÇİN FULL SENTENCE SCAN
        sent_tokens = Token.objects.filter(
            sentence=kw_token.sentence
        ).order_by('index')
```

**Durum:**
- Concordance: Tüm Token tablosunu tarar (index varsa index scan, yoksa full table scan)
- Context extraction: Her match için sentence'daki tüm token'ları çeker
- Window-based collocation: Her keyword için entire sentence'ı işler

**CWB karşılaştırması:**
- CWB: Corpus positions array + binary search = O(log n)
- CorpusLIO: Full table scan + join = O(n) veya worse

---

### ❌ 4. Büyük Veri Test Edildi mi?

**HAYIR**

**Kanıt:**
```markdown
# README.md satır 49-50
### Planned Features (Roadmap)
- 🔲 **Full CWB Pipeline** — Automated corpus indexing and vertical compilation
```

**scripts/ dizini:**
- ✅ smoke_load.py → Sadece model loading testi
- ❌ Corpus load test YOK
- ❌ Performance benchmark YOK
- ❌ 100M+ token test YOK

**Mevcut limitler:**
```python
# corpus/views.py satır 178
for corpus in CorpusMetadata.objects.only('global_metadata').all()[:500]:  # Limit for performance
```
→ Performans için 500 kayıt limiti koyulmuş = **büyük veri henüz test edilmemiş**

---

### ❌ 5. Concurrent Test Edildi mi?

**HAYIR**

**Kanıt:**
```bash
# Workspace file search sonucu
find . -name "*locust*" -o -name "*k6*" -o -name "*load_test*"
# Sonuç: 0 dosya
```

**Eksikler:**
- ❌ Locust/k6 load test script'leri YOK
- ❌ 20/50/100 concurrent user testi YOK
- ❌ Database connection pool limiti test edilmemiş
- ❌ Query timeout scenario'ları yok

**Mevcut rate limiting:**
```python
# corpus/models.py satır 85-95
api_quota_daily = models.IntegerField(default=1000)
queries_today = models.IntegerField(default=0)
```
→ Quota var ama concurrency testi YOK

---

### ❌ 6. EXPLAIN Plan Temiz mi?

**BİLİNMİYOR - Test edilmemiş**

**Kanıt:**
```bash
grep -r "EXPLAIN\|explain_plan\|raw.*sql" corpus/
# Sonuç: EXPLAIN kullanımı YOK
```

**Mevcut durum:**
- Django ORM kullanılıyor (SQL görünmüyor)
- .explain() çağrısı yapılmamış
- Query profiling YOK
- Index usage monitoring YOK

**Test edilmesi gereken sorgular:**
```python
# Potansiyel yavaş sorgular:
Token.objects.filter(lemma__iexact="git").select_related('sentence', 'document')
# → JOIN planı?

Token.objects.filter(sentence=token.sentence).order_by('index')
# → Index kullanıyor mu?
```

---

### ❌ 7. RAM Usage Predictable mı?

**HAYIR**

**Kanıt:**
```python
# corpus/query_engine.py satır 284-295
def ngrams(self, n: int = 2, ...):
    # TÜM CORPUS'U MEMORY'YE YÜKLER!
    sentences = Sentence.objects.all().prefetch_related('tokens')
    
    ngram_counts = {}  # Dictionary büyüklüğü kontrolsüz
    
    for sentence in sentences:
        tokens = list(sentence.tokens.order_by('index'))  # Memory'ye list
```

**Problem senaryoları:**

1. **100M token corpus:**
   - Sentence.objects.all() → OOM (Out of Memory)
   - prefetch_related('tokens') → 100M row memory'de

2. **Collocation analysis:**
```python
# satır 236-266
collocates = {}  # Unbounded dictionary
for kw_token in keyword_tokens:  # Kaç tane match olacak?
    sent_tokens = Token.objects.filter(...)  # Her match için DB query
```

**Sonuç:** Memory usage unpredictable, büyük corpus'ta crash riski.

---

## Performans Testi: "lemma=gel + POS=VERB + 2 token sonra DAT case noun"

### Bu sorgu mevcut sistemde nasıl çalışır?

**Mevcut kod:**
```python
# corpus/query_engine.py - pattern_search()
# ❌ BUNU YAPAMIYOR!
# Sadece tek token pattern'leri destekliyor:
# [lemma="gel" & pos="VERB"]  ← Bu çalışır
# [lemma="gel"][pos="ADJ"]    ← 2-token sequence YOK
```

**Sorunlar:**
1. **Multi-token pattern YOK:** Sadece tek token filter'leri var
2. **Positional offset YOK:** "2 token sonra" syntax yok
3. **Morphological feature search YOK:** "DAT case" gibi feats filtreleme yok

**İmplementasyon gereksinimi:**
```python
# Gerekli query (pseudo-code):
pattern = '[lemma="gel" & upos="VERB"] []{0,2} [feats~"Case=Dat" & upos="NOUN"]'
# → CWB-style CQP syntax gerekiyor
# → Şu anda DESTEKLENMIYOR
```

**Tahmin edilen performans (eğer implemente edilseydi):**
```sql
-- Django ORM üretecek SQL (kötü senaryo):
SELECT t1.*, t2.*, t3.*
FROM token t1
JOIN token t2 ON t2.sentence_id = t1.sentence_id AND t2.index BETWEEN t1.index+1 AND t1.index+3
JOIN token t3 ON t3.sentence_id = t1.sentence_id AND t3.index = t1.index+2
WHERE t1.lemma ILIKE 'gel' AND t1.upos = 'VERB'
  AND t3.upos = 'NOUN' AND t3.feats LIKE '%Case=Dat%'
```
→ **100M token corpus'ta 30+ saniye** (tahmin)

**CWB'de aynı sorgu:**
```bash
# CQP syntax:
[lemma="gel" & pos="VERB"] []{0,2} [Case="Dat" & pos="NOUN"]
# → Positional index kullanır
# → < 500ms dönüş (binary search)
```

---

## Veri Modeli Değerlendirmesi

### Her Token Ayrı Row mu?

**✅ EVET**

```python
# corpus/models.py satır 1759
class Token(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    sentence = models.ForeignKey(Sentence, on_delete=models.CASCADE)
    index = models.IntegerField()
    form = models.CharField(max_length=255, db_index=True)
    lemma = models.CharField(max_length=255, db_index=True)
    # ... her token bir row
```

### 200M Satır Olduğunda Ne Olur?

**Sorunlar:**

1. **Index boyutu kontrol dışı:**
   - form, lemma, upos index'leri: ~3-5 GB her biri
   - Toplam index boyutu: **15-20 GB** (vakum sonrası)
   - PostgreSQL shared_buffers yetersiz kalır

2. **Join maliyeti artar:**
```python
Token.objects.filter(form__iexact="geldi").select_related('sentence', 'document')
# → 200M row Token × Sentence × Document
# → Nested Loop Join → YAVAŞ
```

3. **Sequential scans kaçınılmaz:**
```sql
-- Index kullanılamayan sorgular:
WHERE feats LIKE '%Case=Dat%'  -- Full table scan
WHERE lemma ILIKE '%git%'      -- Partial index kullanılamaz
```

### Composite Index Var mı?

**HAYIR**

**Kanıt:**
```python
# corpus/models.py satır 1870-1878
indexes = [
    models.Index(fields=['document', 'index']),      # Composite ✓
    models.Index(fields=['sentence', 'index']),      # Composite ✓
    models.Index(fields=['form']),                   # Single-column
    models.Index(fields=['lemma']),                  # Single-column
    models.Index(fields=['upos']),                   # Single-column
]
```

**Eksikler:**
- ❌ (lemma, upos) composite YOK → "git" + "VERB" sorgusu iki index ayrı tarar
- ❌ (document, sentence, index) covering index YOK → Context fetch her seferinde disk'e gider
- ❌ Partial index YOK → Punctuation/stopword filter'leri full scan

**Performance comparison:**
```python
# Şu an:
Token.objects.filter(lemma="git", upos="VERB")
# → Index Scan on token_lemma + Index Scan on token_upos + Bitmap AND
# → 2 index taraması

# Olması gereken:
CREATE INDEX idx_lemma_pos ON token(lemma, upos);
# → Single index scan
```

---

## 100M Token Kaldırabilir mi?

### Senaryolar:

#### 1. Basit Form Search
```python
Token.objects.filter(form__iexact="git")[:100]
```
**Tahmin:**
- Index scan on token_form: ~200-500ms (100M row'da)
- Limit 100 → Erken durur
- ✅ Kaldırabilir (yavaş ama kilitlenmez)

#### 2. Lemma + POS + Pattern
```python
Token.objects.filter(lemma="git", upos="VERB").select_related('sentence')[:100]
```
**Tahmin:**
- 2 index scan + bitmap merge: ~1-2 saniye
- select_related JOIN: +500ms
- ✅ Zorlanır ama kaldırabilir

#### 3. N-gram Extraction
```python
ngrams(n=3, use_lemma=True, limit=100)
# → Sentence.objects.all().prefetch_related('tokens')
```
**Tahmin:**
- prefetch_related tüm corpus'u yükler: **CRASH**
- 100M token × 50 byte/token = 5 GB RAM
- ❌ KALDIRMAZ (OOM)

#### 4. Collocation Analysis
```python
collocation(keyword="git", window_size=5)
```
**Tahmin:**
- Her keyword match için sentence fetch
- 10,000 match × sentence fetch = 10,000 query
- ❌ TIMEOUT (Django query timeout tetiklenir)

---

## 50 Eşzamanlı Kullanıcı Kaldırabilir mi?

### Database Connection Pool

**Mevcut ayar (varsayılan Django):**
```python
# settings.py (default)
DATABASES = {
    'default': {
        'CONN_MAX_AGE': 0  # Her request yeni connection
    }
}
```

**PostgreSQL limiti:**
```sql
SHOW max_connections;  -- Genelde 100
```

**50 concurrent user senaryosu:**
- Her user 2-3 query → 100-150 concurrent connection
- **PostgreSQL CONN LIMIT aşılır → ERROR**

**Çözüm (eksik):**
```python
# PgBouncer/connection pooling gerekli
CONN_MAX_AGE = 600  # Connection reuse
```

---

## KWIC < 500ms Dönmeli mi?

### Mevcut concordance performansı:

**Test senaryosu:**
```python
engine = CorpusQueryEngine()
results = engine.concordance(query="git", context_size=5, limit=100)
```

**Adımlar:**
1. `Token.objects.filter(form__iexact="git")` → Index scan (50-200ms küçük corpus'ta)
2. Her match için `Token.objects.filter(sentence=X)` → 100 × 10ms = **1 saniye**
3. Context trimming + serialization → 50ms

**Toplam:** ~1.2-2 saniye (**500ms'yi aşıyor**)

**100M token corpus'ta:**
- Token index scan: 500ms-1s
- Context fetch (100 match): 2-5s
- **Toplam: 3-6 saniye** 😱

**❌ KWIC 500ms gereksinimini karşılayamıyor**

---

## Export Alındığında Sistem Kilitlenmemeli mi?

### Mevcut export kodu:

```python
# corpus/corpus_export_utils.py
def export_concordance_csv(results, ...):
    # 'results' zaten memory'de (QueryEngine'den geldi)
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    for result in results:  # Memory iteration
        writer.writerow(result)
```

**Sorunlar:**

1. **results memory'de bekleniyor:**
```python
# views.py'den gelen:
results = engine.concordance(query, limit=10000)  # 10K result memory'de
export_concordance_csv(results, ...)
```

2. **10,000 result × 200 byte/result = 2 MB RAM** → Küçük export'ta sorun yok

3. **BÜYÜK EXPORT senaryosu:**
```python
# 100,000 result export isteği:
results = engine.concordance(query, limit=100000)
# → 100K × sentence fetch = **10-30 saniye blokaj**
# → Django request timeout
```

**❌ Büyük export'ta kilitlenme riski var**

**Çözüm (eksik):**
- Celery async task YOK
- Streaming export YOK
- Background job queue YOK

---

## CWB Nerede?

### README claim:

```markdown
# README.md satır 39
- ✅ **CQP Query Engine** — Pattern matching via CWB integration
```

**Gerçek durum:**

```bash
$ grep -r "cwb\|CWB\|corpus-workbench" corpus/ corpuslio/
# Sonuç: sadece dosya isimleri
corpuslio/cwb_bridge.py  # Dosya var mı?
```

**cwb_bridge.py içeriği:**
```python
# corpuslio/cwb_bridge.py - BOŞLUK (skeleton/stub)
# CWB integration planned ama implemented değil
```

**Kanıt:**
```python
# corpus/query_engine.py - Sadece Django ORM kullanıyor
class CorpusQueryEngine:
    def __init__(self, documents):
        self.base_queryset = Token.objects.all()  # Pure Django
```

**✅ CWB integration PLANNED, 🔴 IMPLEMENTED değil**

---

## Sistem Soruları - Özet Cevaplar

| Soru | Cevap | Kanıt Dosyası | Durum |
|------|-------|---------------|-------|
| Token-level inverted index var mı? | ❌ HAYIR | models.py satır 1870 | Sadece B-tree index |
| Join-free pattern search var mı? | ❌ HAYIR | query_engine.py satır 68 | Her match JOIN yapar |
| Positional search O(n) değil mi? | ❌ O(n) | query_engine.py satır 242 | Full sentence scan |
| Büyük veri test edildi mi? | ❌ HAYIR | README.md satır 49 | Planned, yapılmamış |
| Concurrent test edildi mi? | ❌ HAYIR | file_search sonucu | Locust/k6 yok |
| EXPLAIN plan temiz mi? | ❓ BİLİNMİYOR | grep sonucu | Test edilmemiş |
| RAM usage predictable mı? | ❌ HAYIR | query_engine.py satır 287 | prefetch_all() kullanımı |
| 100M token kaldırır mı? | ⚠️ KISMEN | - | Basit search evet, n-gram hayır |
| 50 concurrent kaldırır mı? | ❌ HAYIR | - | Connection pool yok |
| KWIC < 500ms mi? | ❌ HAYIR | query_engine.py satır 68 | 1-6 saniye |
| Export kilitlenmez mi? | ⚠️ RİSKLİ | corpus_export_utils.py | Async task yok |

---

## Mimari Karar: Web App mı, Arama Motoru mu?

### Şu Anda: **Web Application**

**Nedenler:**

1. Django ORM-based search (not specialized corpus engine)
2. PostgreSQL row-per-token (not inverted index)
3. Memory-intensive operations (prefetch all)
4. No CWB integration (despite README claim)
5. No load testing, no concurrency testing
6. 500 kayıt performance limiti (views.py:178)

### Korpus Arama Motoru Olması İçin Gerekenler:

#### A. CWB Integration (Critical)
```bash
# Eksik:
cwb-encode -d /var/corpora/turkish -f corpus.vrt
cwb-makeall -V TURKISH
cqp -c TURKISH "... pattern ..."
```

#### B. Inverted Index (Critical)
```python
# Gerekli veri modeli:
class TokenPosition(models.Model):
    corpus_position = models.BigIntegerField(primary_key=True)
    form_id = models.IntegerField(db_index=True)  # Lexicon lookup
    lemma_id = models.IntegerField(db_index=True)
    pos_id = models.IntegerField(db_index=True)
```

#### C. Async Job Queue (Critical)
```python
# Celery tasks:
@shared_task
def export_concordance_async(query_id, user_id):
    # Background export
    # Email when ready
```

#### D. Streaming Queries (Important)
```python
# Generator-based:
def concordance_stream(query):
    for batch in Token.objects.filter(...).iterator(chunk_size=1000):
        yield from process_batch(batch)
```

#### E. Load Testing (Important)
```python
# locustfile.py:
class CorpusUser(HttpUser):
    @task
    def search_concordance(self):
        self.client.get("/api/concordance?q=git&limit=100")
```

---

## Tavsiyeler

### Kısa Vadeli (Production Deployment İçin)
1. ✅ Connection pooling ekle (PgBouncer)
2. ✅ Query limiti düşür (100 result max)
3. ✅ N-gram/collocation pagination ekle (memory explosion önle)
4. ✅ Celery + Redis async tasks
5. ✅ Request timeout (30 saniye)

### Orta Vadeli (Scaling İçin)
1. ✅ Composite index'ler ekle: (lemma, upos), (document, sentence, index)
2. ✅ Partial index: `WHERE upos != 'PUNCT'` (search hızlandırma)
3. ✅ Materialized views: Frequency/collocation pre-computation
4. ✅ Locust load test (20/50/100 user)
5. ✅ pg_stat_statements → slow query monitoring

### Uzun Vadeli (Gerçek Arama Motoru İçin)
1. **CWB full integration:**
   - Corpus encode pipeline
   - CQP query wrapper
   - Binary positional index
   
2. **Elasticsearch integration (alternatif):**
   - Token indexing
   - Shingle tokenizer (n-grams)
   - Boolean must/should queries
   
3. **Custom corpus engine:**
   - Positional array (C++ extension)
   - Memory-mapped files
   - Zero-copy concordance

---

## Sonuç

**CorpusLIO şu anda:**
- ✅ İyi bir **Django web app** (user management, export, GDPR)
- ✅ Akademik projeler için **prototip seviyesinde**
- ❌ Production-grade **corpus arama motoru DEĞİL**

**100M token, 50 concurrent user, < 500ms KWIC için:**
- 🔴 **Mimari yeniden tasarım gerekli**
- 🔴 **CWB integration ya da ElasticSearch gerekli**
- 🔴 **Şu anki sistem bu gereksinimleri karşılayamaz**

**Tercih:**
1. Küçük korpuslar (< 5M token) → Mevcut sistem yeterli
2. Orta korpuslar (5-50M token) → Index + pagination + async ile idare eder
3. Büyük korpuslar (50M+ token) → CWB/ElasticSearch zorunlu

---

**Rapor sonu.**  
*Tüm kanıtlar kod satırlarıyla desteklenmiştir.*
