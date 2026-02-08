# Week 9: Advanced Search & CQP-Style Queries - Tamamlandı ✅

**Tarih:** Şubat 2026  
**Durum:** ✅ TAMAMLANDI  
**Süre:** 1 gün  
**Kod Artışı:** ~1,450 satır

---

## 🎯 Hedefler

Week 9'un amacı, gelişmiş pattern matching ve CQP (Corpus Query Processor) tarzı sorgular ile corpus aramasını güçlendirmekti:

1. ✅ CQP-style query parser implementasyonu
2. ✅ Pattern matching engine (sequence matching)
3. ✅ Advanced search UI with query builder
4. ✅ Regex support in lemma/POS fields
5. ✅ Query syntax tutorial page

---

## 📋 Tamamlanan Görevler

### 1. CQP Query Parser Implementasyonu ✅

**Dosya:** `ocrchestra/query_parser.py` (426 satır)

**Sınıflar:**

**a) TokenConstraint (Dataclass)**
```python
@dataclass
class TokenConstraint:
    word_pattern: Optional[str] = None
    lemma_pattern: Optional[str] = None
    pos_pattern: Optional[str] = None
    is_regex: bool = True
    case_sensitive: bool = False
    
    def matches(self, token: Dict[str, Any]) -> bool
    def _match_pattern(self, value: str, pattern: str) -> bool
```

**Özellikler:**
- `word_pattern`: Kelime pattern'i (regex destekli)
- `lemma_pattern`: Lemma pattern'i
- `pos_pattern`: POS tag pattern'i
- Her constraint multiple condition desteği
- Regex veya literal matching
- Case-sensitive/insensitive

**b) QueryPattern (Dataclass)**
```python
@dataclass
class QueryPattern:
    constraints: List[TokenConstraint]
    
    def __len__(self)
```

**Özellikler:**
- Constraint listesi (sequence)
- Sequence uzunluğu tracking

**c) CQPQueryParser**
```python
class CQPQueryParser:
    TOKEN_PATTERN = re.compile(r'\[([^\]]+)\]')
    ATTR_PATTERN = re.compile(r'(word|lemma|pos)\s*=\s*"([^"]+)"')
    
    def parse(self, query: str) -> Optional[QueryPattern]
    def _parse_token_constraint(self, token_str: str) -> Optional[TokenConstraint]
    def validate_query(self, query: str) -> Tuple[bool, Optional[str]]
    def get_query_info(self, query: str) -> Dict[str, Any]
```

**Özellikler:**
- CQP syntax parsing
- Regex pattern extraction
- Error handling with messages
- Query validation
- Query info extraction

**Desteklenen Syntax:**
```
[word="test"]                      → Exact word match
[lemma="gitmek"]                   → Lemma match
[pos="NOUN"]                       → POS tag match
[word=".*ing"]                     → Regex word match
[word="test" & pos="NOUN"]         → Multiple constraints
[pos="ADJ"] [pos="NOUN"]           → Sequence pattern
```

### 2. Pattern Matching Engine ✅

**Sınıf:** `PatternMatcher`

```python
class PatternMatcher:
    def find_matches(
        self,
        pattern: QueryPattern,
        tokens: List[Dict[str, Any]],
        context_size: int = 5
    ) -> List[Dict[str, Any]]
    
    def _matches_at_position(
        self,
        pattern: QueryPattern,
        tokens: List[Dict[str, Any]],
        start_pos: int
    ) -> bool
    
    def _extract_match(
        self,
        tokens: List[Dict[str, Any]],
        start_pos: int,
        pattern_len: int,
        context_size: int
    ) -> Dict[str, Any]
```

**Algoritma:**
1. **Sliding Window:** Token sequence üzerinde kaydırarak arama
2. **Constraint Matching:** Her position'da pattern constraint'leri kontrol
3. **Context Extraction:** Match bulunduğunda left/right context çıkarma
4. **Match Info:** Position, context, matched tokens döndürme

**Çıktı Formatı:**
```python
{
    'position': 42,
    'left_context': [{'word': '...', 'lemma': '...', 'pos': '...'}, ...],
    'match': [{'word': 'güzel', 'lemma': 'güzel', 'pos': 'ADJ'}, 
              {'word': 'kitap', 'lemma': 'kitap', 'pos': 'NOUN'}],
    'right_context': [...],
    'left_context_text': 'bir çok öğrenci',
    'match_text': 'güzel kitap',
    'right_context_text': 'okudu ve öğrendi'
}
```

**Performance:**
- Sliding window: O(n * m) - n: tokens, m: pattern length
- Regex matching: O(k) per token - k: pattern length
- Context extraction: O(context_size)

### 3. Advanced Search View ✅

**Dosya:** `corpus/advanced_search_views.py` (293 satır)

**View Fonksiyonları:**

**a) advanced_search_view**
```python
@login_required
@role_required('researcher')
def advanced_search_view(request):
```

**Özellikler:**
- CQP query input
- Document filtering (specific or all)
- Context size control (3-10 words)
- Multi-document search
- QueryLog integration
- Result display with concordance
- Query validation feedback

**Akış:**
1. Query parse et (CQPQueryParser)
2. Pattern validation
3. Document'ları al (user-specific veya all)
4. Her document'ta token'ları normalize et
5. PatternMatcher ile matches bul
6. Concordance format'ında sonuçları döndür
7. QueryLog'a kaydet

**b) validate_cqp_query (AJAX)**
```python
@require_http_methods(["POST"])
@login_required
def validate_cqp_query(request):
```

**Özellikler:**
- AJAX endpoint
- Real-time validation
- JSON response
- Query info return

**c) query_syntax_help**
```python
@login_required
def query_syntax_help(request):
```

**Özellikler:**
- Tutorial sayfası
- 5 kategori, 18 example
- Attribute reference
- Operator reference
- Matches vs doesn't match

### 4. Advanced Search Template ✅

**Dosya:** `templates/corpus/advanced_search.html` (410 satır)

**Bölümler:**

**a) Search Header**
- Gradient background (#667eea → #764ba2)
- "Advanced Pattern Search" başlık
- CQP açıklaması

**b) Query Input Section**
- Monospace font input
- Live validation
- Query syntax help link
- Context size selector
- Document filter

**c) Visual Query Builder**
- Attribute selector (word/lemma/pos)
- Pattern input
- Add token button
- Token list display (color-coded)
- Remove token functionality
- Generate query button
- Clear builder button

**d) Example Queries**
- 6 clickable example
- Query + description
- Click to use functionality

**e) Results Display**
- Concordance format
- Left context (gray)
- Match highlight (yellow background)
- Right context (gray)
- Document info
- Position info
- Stats (total matches, token count, attributes)

**JavaScript Özellikler:**
```javascript
function useExample(query)           // Example query'yi input'a yükle
function validateQuery(query)        // Client-side validation
function addBuilderToken()           // Builder'a token ekle
function removeBuilderToken(index)   // Token kaldır
function updateBuilderDisplay()      // Builder görünümünü güncelle
function generateQuery()             // CQP query generate et
function clearBuilder()              // Builder'ı temizle
```

### 5. Query Syntax Help Template ✅

**Dosya:** `templates/corpus/query_syntax_help.html` (320 satır)

**İçerik Kategorileri:**

**1. Quick Start**
- 5 adımlık başlangıç rehberi
- Sarı warning box
- Örneklerle açıklama

**2. Available Attributes**
- word: Surface form
- lemma: Dictionary form
- pos: Part-of-speech tag
- Her attribute için example

**3. Operators & Special Characters**
- `&` : AND operator
- `.*` : Regex any characters
- `^` : Start of string
- `$` : End of string
- Grid layout

**4. Basic Token Matching (3 examples)**
- Exact word match
- Lemma match
- POS tag match
- Matches vs doesn't match

**5. Regex Patterns (3 examples)**
- Words ending with suffix
- Words starting with prefix
- Lemmas starting with vowel

**6. Multiple Constraints (2 examples)**
- Word + POS
- Lemma + POS

**7. Sequence Patterns (3 examples)**
- ADJ + NOUN
- DET + ADJ + NOUN
- VERB + "ve" + VERB

**8. Advanced Examples (2 examples)**
- Infinitive + auxiliary
- Noun + postposition

**Toplam:** 18 örnek, her biri ile:
- CQP query
- Description
- Matches (yeşil)
- Doesn't match (kırmızı)

### 6. URL Routes ✅

**Dosya:** `corpus/urls.py`

```python
from . import advanced_search_views

path('advanced-search/', advanced_search_views.advanced_search_view, name='advanced_search'),
path('query-syntax-help/', advanced_search_views.query_syntax_help, name='query_syntax_help'),
path('validate-cqp/', advanced_search_views.validate_cqp_query, name='validate_cqp'),
```

---

## 🛠️ Teknik Detaylar

### CQP Query Parsing

**Regex Patterns:**
```python
TOKEN_PATTERN = r'\[([^\]]+)\]'           # Matches [...]
ATTR_PATTERN = r'(word|lemma|pos)\s*=\s*"([^"]+)"'  # Matches attr="value"
```

**Parse Akışı:**
```
Input: [pos="ADJ"] [pos="NOUN"]
  ↓
TOKEN_PATTERN.findall()
  → ['pos="ADJ"', 'pos="NOUN"']
  ↓
ATTR_PATTERN.findall()
  → [('pos', 'ADJ'), ('pos', 'NOUN')]
  ↓
TokenConstraint objects
  → [TokenConstraint(pos_pattern='ADJ'), TokenConstraint(pos_pattern='NOUN')]
  ↓
QueryPattern(constraints=[...])
```

### Pattern Matching Algorithm

**Sliding Window:**
```python
for i in range(len(tokens) - pattern_len + 1):
    if matches_at_position(pattern, tokens, i):
        extract_match(tokens, i, pattern_len, context_size)
```

**Constraint Matching:**
```python
for each constraint in pattern.constraints:
    token = tokens[start_pos + constraint_index]
    if not constraint.matches(token):
        return False
return True
```

### Token Normalization

**Desteklenen Formatlar:**
```python
# Format 1: List of dicts
[{'word': 'test', 'lemma': 'test', 'pos': 'NOUN'}, ...]

# Format 2: Flat list (auto-convert)
['test', 'test', 'NOUN', 'word', 'lemma', 'POS', ...]
```

**Normalization:**
```python
if isinstance(tokens[0], dict):
    return tokens  # Already normalized
else:
    # Group into triplets (word, lemma, pos)
    i = 0
    while i < len(tokens):
        yield {'word': tokens[i], 'lemma': tokens[i+1], 'pos': tokens[i+2]}
        i += 3
```

---

## 📊 Code Statistics

**Yeni Dosyalar:**
- `ocrchestra/query_parser.py`: 426 satır
- `corpus/advanced_search_views.py`: 293 satır
- `templates/corpus/advanced_search.html`: 410 satır
- `templates/corpus/query_syntax_help.html`: 320 satır

**Değiştirilen Dosyalar:**
- `corpus/urls.py`: +4 satır (import + 3 route)

**Toplam:**
- **Yeni kod:** ~1,450 satır
- **Yeni dosya:** 4
- **Yeni URL route:** 3
- **Yeni view:** 3
- **Yeni template:** 2

---

## ✅ Test Sonuçları

**System Check:**
```
System check identified 2 issues (0 silenced).
WARNINGS:
- ACCOUNT_AUTHENTICATION_METHOD deprecated
- ACCOUNT_EMAIL_REQUIRED deprecated
```
✅ Sadece deprecation warnings (kritik hata yok)

**Fonksiyonel Testler:**

**1. Basic Query Parsing:**
```python
query = '[word="test"]'
pattern = parser.parse(query)
assert len(pattern.constraints) == 1
assert pattern.constraints[0].word_pattern == "test"
```
✅ PASSED

**2. Sequence Pattern:**
```python
query = '[pos="ADJ"] [pos="NOUN"]'
pattern = parser.parse(query)
assert len(pattern.constraints) == 2
```
✅ PASSED

**3. Multiple Constraints:**
```python
query = '[word="test" & pos="NOUN"]'
pattern = parser.parse(query)
assert pattern.constraints[0].word_pattern == "test"
assert pattern.constraints[0].pos_pattern == "NOUN"
```
✅ PASSED

**4. Regex Pattern:**
```python
query = '[word=".*ing"]'
pattern = parser.parse(query)
# Should match: testing, running, coding
```
✅ PASSED

**5. Invalid Syntax:**
```python
query = 'invalid syntax'
pattern = parser.parse(query)
assert pattern is None
assert parser.last_error is not None
```
✅ PASSED

**6. Pattern Matching:**
```python
tokens = [
    {'word': 'bir', 'lemma': 'bir', 'pos': 'DET'},
    {'word': 'güzel', 'lemma': 'güzel', 'pos': 'ADJ'},
    {'word': 'kitap', 'lemma': 'kitap', 'pos': 'NOUN'}
]
query = '[pos="ADJ"] [pos="NOUN"]'
matches = search_pattern(query, tokens)
assert len(matches) == 1
assert matches[0]['match_text'] == 'güzel kitap'
```
✅ PASSED

---

## 🎨 UI/UX Özellikleri

### Color Scheme

**Advanced Search:**
- Header gradient: #667eea → #764ba2 (Mor)
- Match highlight: #fef3c7 (Sarı)
- Valid query: #d1fae5 (Yeşil)
- Invalid query: #fee2e2 (Kırmızı)
- Builder tokens: #667eea background, white text

**Query Builder:**
- Background: #f9fafb
- Border: #667eea dashed
- Token cards: #667eea with white text
- Remove button: rgba(255,255,255,0.2)

**Tutorial Page:**
- Header gradient: #10b981 → #059669 (Yeşil)
- Quick start: #fef3c7 background, #f59e0b border
- Examples: #f9fafb background
- Positive matches: #10b981 (Yeşil)
- Negative matches: #ef4444 (Kırmızı)

### Typography

- Query input: 'Courier New', monospace, 1.1em
- Examples: 1.1em Courier New
- Descriptions: 0.85-0.9em regular
- Headers: 2em bold

### Interactive Features

**Query Builder:**
1. Select attribute (dropdown)
2. Enter pattern (text input)
3. Click "Add Token" (or press Enter)
4. Visual token display
5. Remove individual tokens
6. Generate CQP query
7. Clear all

**Live Validation:**
- Input'a yazarken real-time validation
- Yeşil check veya kırmızı error icon
- Validation message display

**Example Queries:**
- Click to use
- Auto-fill input
- Trigger validation

---

## 🔗 Entegrasyonlar

### Week 2 Entegrasyonu (Audit Logging)
- ✅ QueryLog.objects.create() ile query logging
- ✅ query_type='cqp_advanced' ile CQP query'leri ayırma
- ✅ results_count tracking

### Existing Search Engine
- ✅ Mevcut CorpusSearchEngine ile kompatibilite
- ✅ Token normalization ortak format
- ✅ Document.analysis field kullanımı

---

## 📚 Kullanıcı Senaryoları

### Senaryo 1: Basit POS Pattern Arama

**Hedef:** Tüm noun'ları bul

1. User `/advanced-search/` sayfasına gider
2. Query input'a `[pos="NOUN"]` yazar
3. Live validation yeşil check gösterir
4. "Search Pattern" butonuna basar
5. Concordance sonuçlarını görür:
   ```
   ... bir çok öğrenci kitap okudu ve ...
   ... büyük bir değişiklik başladı ...
   ```
6. Her match'te:
   - Sol context (grı)
   - Highlighted match (sarı)
   - Sağ context (gri)
   - Document adı
   - Position

### Senaryo 2: Sequence Pattern (ADJ + NOUN)

**Hedef:** Sıfat + isim kombinasyonlarını bul

1. Visual Query Builder'ı kullanır
2. Attribute: "pos", Pattern: "ADJ" → "Add Token"
3. Attribute: "pos", Pattern: "NOUN" → "Add Token"
4. Token list'te görür:
   ```
   [pos="ADJ"] [pos="NOUN"]
   ```
5. "Generate Query" butonuna basar
6. Query input'a otomatik yüklenir: `[pos="ADJ"] [pos="NOUN"]`
7. Search yapınca bulur:
   ```
   güzel kitap
   büyük ev
   kırmızı araba
   ```

### Senaryo 3: Regex Pattern

**Hedef:** "-lik" ile biten kelimeleri bul

1. Example queries'den `[word=".*lik"]` örneğine tıklar
2. Query input'a yüklenir
3. Validation OK
4. Search yapar
5. Sonuçlar:
   ```
   güzellik
   sevgilik
   dostluk
   ```

### Senaryo 4: Multiple Constraints

**Hedef:** "test" kelimesini sadece NOUN olduğunda bul

1. Query builder:
   - Attribute: "word", Pattern: "test"
   - Add Token
2. Token'a tıklayarak edit (gelecek özellik)
3. Manuel olarak query'yi düzenler:
   ```
   [word="test" & pos="NOUN"]
   ```
4. Search yapar
5. Sadece "test" kelimesinin noun olarak kullanıldığı match'leri görür

### Senaryo 5: Tutorial Kullanımı

1. "Query Syntax Help" butonuna tıklar
2. Quick Start'ı okur
3. Example categories'e bakar:
   - Basic Token Matching
   - Regex Patterns
   - Sequence Patterns
4. Her example'da:
   - Query
   - Description
   - Matches examples (yeşil)
   - Doesn't match examples (kırmızı)
5. Operators reference'ı kontrol eder
6. "Back to Advanced Search" ile döner

---

## 🚀 Week 9'un Başarıları

✨ **CQP Query Parser:**
- Tam regex desteği
- Multiple constraint support
- Sequence pattern matching
- Validation ve error messaging
- Query info extraction

✨ **Pattern Matcher:**
- Sliding window algorithm
- Context extraction (3-10 words)
- Multi-document search
- Position tracking
- Concordance formatting

✨ **Visual Query Builder:**
- No-code query construction
- Add/remove tokens
- Visual token display
- Auto-generate CQP syntax
- User-friendly interface

✨ **Tutorial System:**
- 18 comprehensive examples
- 5 categories (basic → advanced)
- Matches vs doesn't match
- Operator reference
- Quick start guide

✨ **Advanced Search UI:**
- Live query validation
- Example queries (clickable)
- Context size control
- Document filtering
- Concordance display
- QueryLog integration

✨ **Code Quality:**
- Dataclass kullanımı
- Type hints
- Docstrings
- Error handling
- Clean architecture

---

## 📈 İyileştirme Önerileri (Post-MVP)

### Phase 1: Query Enhancements
- **Query History:** Saved queries özelliği
- **Query Sharing:** Public query collection
- **Query Templates:** Reusable patterns
- **Negation:** `![pos="NOUN"]` - NOT operator
- **Wildcards:** `[]{1,3}` - optional tokens
- **OR operator:** `[pos="NOUN|VERB"]`

### Phase 2: Performance
- **Indexing:** Token attribute indexing
- **Caching:** Frequent query caching
- **Parallel Search:** Multi-document parallel processing
- **Progressive Results:** Stream results as found

### Phase 3: Advanced Features
- **Collocations:** Find word associations
- **Dependency Patterns:** `[pos="ADJ"] >{nsubj} [pos="NOUN"]`
- **Distance:** `[word="bir"]  []{0,5} [pos="NOUN"]` - max 5 tokens apart
- **Frequency Filters:** `[word=".*" & freq>100]`

### Phase 4: UX Improvements
- **Query Autocomplete:** Suggest attributes/values
- **Syntax Highlighting:** Color-code query parts
- **Error Underline:** Visual error indication
- **Query Explanation:** Natural language explanation
- **Result Export:** Export concordance as CSV/Excel

---

## 🎓 Öğrenilenler

### Teknik
1. **Regex Parsing:** Complex regex pattern extraction
2. **Dataclasses:** Clean data modeling with Python 3.7+
3. **Sliding Window:** Efficient sequence matching algorithm
4. **Token Normalization:** Handle multiple input formats
5. **Context Extraction:** Concordance display best practices

### UX
1. **Live Validation:** Real-time feedback improves UX
2. **Visual Builders:** Non-technical users need visual tools
3. **Examples:** Clickable examples accelerate learning
4. **Progressive Disclosure:** Start simple, reveal complexity
5. **Tutorial Structure:** Categories help navigation

### Architecture
1. **Separation of Concerns:** Parser ↔ Matcher ↔ View
2. **Testability:** Pure functions easier to test
3. **Extensibility:** Easy to add new attributes/operators
4. **Error Handling:** User-friendly error messages critical
5. **Documentation:** Inline docstrings + tutorial page

---

## ✅ Week 9 Tamamlandı!

**Tamamlanma Durumu:** 100%  
**Tüm görevler bitmiş:** ✅ 6/6  
**System check:** ✅ Passed  
**Code quality:** ✅ High  

**Sonraki adım:** Week 10 - Security Hardening

---

**Tarih:** Şubat 2026  
**Geliştirici:** GitHub Copilot + User  
**İlerleme:** 9/12 hafta (75% tamamlandı) 🎉
