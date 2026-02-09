# OCRchestra API Kılavuzu

**Versiyon:** 1.0  
**Base URL:** `https://api.ocrchestra.tr/v1/`  
**Tarih:** Şubat 2026

---

## 📑 İçindekiler

1. [Giriş](#giriş)
2. [Authentication](#authentication)
3. [Rate Limiting](#rate-limiting)
4. [Endpoints](#endpoints)
   - [Corpus Search](#corpus-search)
   - [Analysis](#analysis)
   - [Export](#export)
   - [Collections](#collections)
   - [User](#user)
5. [Response Format](#response-format)
6. [Error Handling](#error-handling)
7. [Code Examples](#code-examples)
8. [SDKs](#sdks)
9. [Changelog](#changelog)

---

## Giriş

### API'ye Kimler Erişebilir?

OCRchestra REST API, **Developer** ve **Admin** rollerine sahip kullanıcılara açıktır.

**Gereksinimler:**
- Doğrulanmış araştırmacı hesabı (Verified Researcher)
- API key başvurusu (developer@ocrchestra.tr)
- Onaylanmış API key

### API Key Alma

**Adımlar:**
```
1. developer@ocrchestra.tr adresine e-posta gönderin
2. Konu: "API Key Başvurusu - [Proje Adı]"
3. E-postada belirtin:
   - Tam adınız ve kurumunuz
   - Proje açıklaması
   - Beklenen kullanım miktarı (request/gün)
   - Mevcut OCRchestra kullanıcı adınız
4. 5-7 iş günü içinde inceleme
5. Onay sonrası API key e-posta ile gönderilir
```

### Base URL

**Production:**
```
https://api.ocrchestra.tr/v1/
```

**Sandbox (Test):**
```
https://sandbox-api.ocrchestra.tr/v1/
```

**Not:** Sandbox aynı endpoint'leri kullanır ama test verisi ile. Production'da kota harcanmaz.

---

## Authentication

### API Key Authentication

**Header Format:**
```http
Authorization: Bearer YOUR_API_KEY_HERE
```

**Örnek Request:**
```bash
curl -X GET "https://api.ocrchestra.tr/v1/search?q=dilbilim" \
  -H "Authorization: Bearer ocrch_1234567890abcdef" \
  -H "Content-Type: application/json"
```

### API Key Güvenliği

**✅ Yapın:**
- API key'i environment variable'da saklayın
- HTTPS kullanın (HTTP kabul edilmez)
- Düzenli olarak key'i rotate edin
- Farklı projeler için farklı key'ler alın

**❌ Yapmayın:**
- Client-side kod'da (JavaScript) kullanmayın
- Public repository'de paylaşmayın
- Log dosyalarına yazmayın
- Email veya chat'te gönderi

### Key Rotation

**Mevcut Key'i Yenileme:**
```http
POST /v1/user/api-key/rotate
Authorization: Bearer OLD_KEY

Response:
{
  "old_key": "ocrch_1234...def",
  "new_key": "ocrch_9876...abc",
  "valid_until": "2026-03-09T00:00:00Z",
  "grace_period_days": 30
}
```

**Grace Period:** Eski key 30 gün daha çalışır, bu sürede uygulamalarınızı güncelleyin.

---

## Rate Limiting

### Limitler

| Rol       | Request/Dakika | Request/Gün | Export/Gün | Export MB/Ay |
|-----------|----------------|-------------|------------|--------------|
| Developer | 100            | 2,000       | 50         | 100 MB       |
| Admin     | ∞              | ∞           | ∞          | ∞            |

### Rate Limit Headers

**Her Response'da:**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1707475200
```

**Aşıldığında (429 Too Many Requests):**
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit aşıldı. Lütfen 42 saniye bekleyin.",
    "retry_after": 42,
    "limit": 100,
    "reset_at": "2026-02-09T10:30:00Z"
  }
}
```

### Best Practices

**Exponential Backoff:**
```python
import time

def api_request_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url, headers={"Authorization": f"Bearer {API_KEY}"})
        
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            wait_time = retry_after * (2 ** attempt)
            print(f"Rate limited. Waiting {wait_time}s...")
            time.sleep(wait_time)
            continue
        
        return response
    
    raise Exception("Max retries exceeded")
```

---

## Endpoints

### Corpus Search

#### Search Documents

**Endpoint:** `GET /search`

**Açıklama:** Korpusta kelime arama yapar, concordance sonuçları döner.

**Query Parameters:**
| Parametre | Tip     | Zorunlu | Açıklama                                    |
|-----------|---------|---------|---------------------------------------------|
| `q`       | string  | Evet    | Arama sorgusu                               |
| `regex`   | boolean | Hayır   | Regex modu (default: false)                 |
| `fuzzy`   | boolean | Hayır   | Fuzzy search (default: false)               |
| `context` | integer | Hayır   | Bağlam penceresi (5-100, default: 20)       |
| `limit`   | integer | Hayır   | Sonuç sayısı (1-1000, default: 100)         |
| `offset`  | integer | Hayır   | Pagination offset (default: 0)              |
| `collection` | string | Hayır | Koleksiyon ID (null = tüm korpus)           |

**Örnek Request:**
```http
GET /v1/search?q=dilbilim&limit=10&context=30 HTTP/1.1
Host: api.ocrchestra.tr
Authorization: Bearer ocrch_1234567890abcdef
```

**Response (200 OK):**
```json
{
  "query": {
    "text": "dilbilim",
    "regex": false,
    "fuzzy": false,
    "context_size": 30,
    "collection": null
  },
  "metadata": {
    "total_matches": 1247,
    "returned": 10,
    "offset": 0,
    "execution_time_ms": 42
  },
  "results": [
    {
      "id": "match_001",
      "left_context": "Türk dili ve edebiyatı bölümünde",
      "keyword": "dilbilim",
      "right_context": "dersleri büyük ilgi görüyor",
      "document": {
        "id": "doc_12345",
        "filename": "turkce_arastirmalari.pdf",
        "position": 1203,
        "page": 7
      }
    }
    // ... 9 more results
  ],
  "facets": {
    "by_document": [
      {"doc_id": "doc_12345", "count": 47},
      {"doc_id": "doc_67890", "count": 23}
    ],
    "by_year": [
      {"year": 2020, "count": 345},
      {"year": 2021, "count": 412}
    ]
  }
}
```

#### Advanced Search

**Endpoint:** `POST /search/advanced`

**Açıklama:** Kompleks sorgular için gelişmiş arama.

**Request Body:**
```json
{
  "query": {
    "operator": "AND",
    "terms": [
      {"text": "dilbilim", "field": "content"},
      {"text": "Türkçe", "field": "content"}
    ]
  },
  "filters": {
    "document_type": ["pdf", "docx"],
    "date_range": {
      "start": "2020-01-01",
      "end": "2025-12-31"
    },
    "tags": ["linguistics", "turkish"]
  },
  "options": {
    "context_size": 50,
    "limit": 100,
    "offset": 0,
    "sort": "relevance"
  }
}
```

**Response:** Same format as GET /search

---

### Analysis

#### Frequency Analysis

**Endpoint:** `POST /analysis/frequency`

**Açıklama:** Kelime frekans analizi yapar.

**Request Body:**
```json
{
  "collection_id": "coll_abc123",
  "options": {
    "min_frequency": 5,
    "max_results": 100,
    "exclude_stopwords": true,
    "lowercase": true
  }
}
```

**Response (200 OK):**
```json
{
  "collection": {
    "id": "coll_abc123",
    "name": "19. Yüzyıl Romanları",
    "total_tokens": 1245678,
    "unique_tokens": 34521
  },
  "statistics": {
    "type_token_ratio": 0.0277,
    "top_10_coverage": 0.42
  },
  "frequencies": [
    {"word": "ve", "count": 12543, "percentage": 1.007},
    {"word": "bir", "count": 8721, "percentage": 0.700},
    {"word": "bu", "count": 6912, "percentage": 0.555}
    // ... more items
  ]
}
```

#### N-gram Analysis

**Endpoint:** `POST /analysis/ngram`

**Request Body:**
```json
{
  "collection_id": "coll_abc123",
  "n": 2,
  "options": {
    "min_frequency": 10,
    "max_results": 50
  }
}
```

**Response (200 OK):**
```json
{
  "collection": {"id": "coll_abc123", "name": "19. Yüzyıl Romanları"},
  "n": 2,
  "ngrams": [
    {"ngram": ["bu", "nedenle"], "count": 145},
    {"ngram": ["diğer", "taraftan"], "count": 98}
  ]
}
```

#### Collocation Analysis

**Endpoint:** `POST /analysis/collocation`

**Request Body:**
```json
{
  "keyword": "kahve",
  "window_size": 5,
  "collection_id": null,
  "options": {
    "min_frequency": 5,
    "statistical_measure": "MI"
  }
}
```

**Statistical Measures:**
- `MI`: Mutual Information
- `T`: T-score
- `DICE`: Dice coefficient
- `LOG_LIKELIHOOD`: Log-likelihood ratio

**Response (200 OK):**
```json
{
  "keyword": "kahve",
  "window_size": 5,
  "total_occurrences": 347,
  "collocations": [
    {
      "word": "türk",
      "count": 37,
      "score": 8.23,
      "position": "L1"
    },
    {
      "word": "içmek",
      "count": 28,
      "score": 7.91,
      "position": "R1"
    }
  ]
}
```

---

### Export

#### Create Export

**Endpoint:** `POST /export`

**Açıklama:** Export işi oluşturur, arka planda işlenir.

**Request Body:**
```json
{
  "type": "concordance",
  "format": "csv",
  "search_query": {
    "q": "dilbilim",
    "collection_id": null
  },
  "options": {
    "include_metadata": true,
    "watermark": true,
    "context_size": 30
  }
}
```

**Export Types:**
- `concordance`: KWIC sonuçları
- `frequency`: Frekans listesi
- `ngram`: N-gram analizi
- `collocation`: Kollokasyon listesi
- `full_collection`: Tam koleksiyon export

**Formats:**
- `csv`: Comma-separated values
- `json`: JSON format
- `xlsx`: Excel workbook (sadece Developer+)

**Response (202 Accepted):**
```json
{
  "export_id": "exp_xyz789",
  "status": "queued",
  "created_at": "2026-02-09T10:15:00Z",
  "estimated_completion": "2026-02-09T10:16:30Z",
  "download_url": null
}
```

#### Check Export Status

**Endpoint:** `GET /export/{export_id}`

**Response (200 OK):**
```json
{
  "export_id": "exp_xyz789",
  "status": "completed",
  "created_at": "2026-02-09T10:15:00Z",
  "completed_at": "2026-02-09T10:16:12Z",
  "download_url": "https://exports.ocrchestra.tr/exp_xyz789.csv",
  "expires_at": "2026-03-11T10:16:12Z",
  "file_size_bytes": 245670,
  "metadata": {
    "rows": 1247,
    "format": "csv",
    "watermarked": true
  }
}
```

**Status Values:**
- `queued`: İşlem sıraya alındı
- `processing`: İşleniyor
- `completed`: Tamamlandı, indirilmeye hazır
- `failed`: Hata oluştu
- `expired`: Süre doldu (30 gün)

#### Download Export

**Endpoint:** `GET /export/{export_id}/download`

**Response:** Binary file (CSV/JSON/XLSX)

**Headers:**
```http
Content-Type: text/csv; charset=utf-8
Content-Disposition: attachment; filename="ocrchestra_export_exp_xyz789.csv"
Content-Length: 245670
```

---

### Collections

#### List Collections

**Endpoint:** `GET /collections`

**Query Parameters:**
| Parametre    | Tip    | Açıklama                          |
|--------------|--------|-----------------------------------|
| `visibility` | string | public, shared, private           |
| `limit`      | int    | Sayfa başına sonuç (default: 20)  |
| `offset`     | int    | Pagination offset                 |

**Response (200 OK):**
```json
{
  "total": 47,
  "limit": 20,
  "offset": 0,
  "collections": [
    {
      "id": "coll_abc123",
      "name": "19. Yüzyıl Türk Romanları",
      "description": "1850-1900 arası yazılmış romanlar",
      "visibility": "public",
      "owner": {
        "username": "researcher123",
        "institution": "İstanbul Üniversitesi"
      },
      "statistics": {
        "document_count": 47,
        "total_tokens": 1245678,
        "created_at": "2025-11-15T08:30:00Z",
        "updated_at": "2026-01-20T14:22:00Z"
      }
    }
    // ... more collections
  ]
}
```

#### Get Collection Details

**Endpoint:** `GET /collections/{collection_id}`

**Response (200 OK):**
```json
{
  "id": "coll_abc123",
  "name": "19. Yüzyıl Türk Romanları",
  "description": "1850-1900 arası yazılmış romanlar",
  "visibility": "public",
  "owner": {
    "id": "usr_456",
    "username": "researcher123",
    "institution": "İstanbul Üniversitesi"
  },
  "statistics": {
    "document_count": 47,
    "total_tokens": 1245678,
    "unique_tokens": 34521,
    "type_token_ratio": 0.0277,
    "avg_document_length": 26503
  },
  "documents": [
    {
      "id": "doc_12345",
      "filename": "intibah.pdf",
      "author": "Namık Kemal",
      "year": 1876,
      "tokens": 45231
    }
    // ... more documents
  ],
  "tags": ["edebiyat", "roman", "19yy", "osmanlı"],
  "created_at": "2025-11-15T08:30:00Z",
  "updated_at": "2026-01-20T14:22:00Z"
}
```

#### Create Collection

**Endpoint:** `POST /collections`

**Request Body:**
```json
{
  "name": "Modern Türk Şiiri",
  "description": "1923 sonrası Türk şiiri örnekleri",
  "visibility": "private",
  "document_ids": ["doc_111", "doc_222", "doc_333"],
  "tags": ["şiir", "modern", "cumhuriyet"]
}
```

**Response (201 Created):**
```json
{
  "id": "coll_new456",
  "name": "Modern Türk Şiiri",
  "message": "Koleksiyon başarıyla oluşturuldu",
  "document_count": 3
}
```

#### Update Collection

**Endpoint:** `PATCH /collections/{collection_id}`

**Request Body:**
```json
{
  "name": "Modern Türk Şiiri (Güncel)",
  "visibility": "public",
  "add_documents": ["doc_444"],
  "remove_documents": ["doc_111"]
}
```

#### Delete Collection

**Endpoint:** `DELETE /collections/{collection_id}`

**Response (204 No Content)**

**Not:** Sadece koleksiyon silinir, belgeler korunur.

---

### User

#### Get API Usage

**Endpoint:** `GET /user/usage`

**Response (200 OK):**
```json
{
  "user": {
    "username": "researcher123",
    "role": "developer",
    "api_key_status": "active"
  },
  "quota": {
    "requests": {
      "limit_per_minute": 100,
      "limit_per_day": 2000,
      "used_today": 347,
      "remaining_today": 1653,
      "reset_at": "2026-02-10T00:00:00Z"
    },
    "exports": {
      "limit_per_day": 50,
      "limit_mb_per_month": 100,
      "used_today": 12,
      "used_mb_this_month": 34.5,
      "remaining_mb": 65.5
    }
  },
  "statistics": {
    "total_requests_lifetime": 12573,
    "total_exports_lifetime": 423,
    "most_searched_term": "dilbilim"
  }
}
```

#### Get API Key Info

**Endpoint:** `GET /user/api-key`

**Response (200 OK):**
```json
{
  "key_id": "key_abc123",
  "key_prefix": "ocrch_1234",
  "created_at": "2025-10-15T09:00:00Z",
  "last_used_at": "2026-02-09T10:15:23Z",
  "expires_at": null,
  "permissions": ["search", "analysis", "export", "collections"],
  "rate_limit_tier": "developer"
}
```

---

## Response Format

### Success Response

**Standard Structure:**
```json
{
  "metadata": {
    "timestamp": "2026-02-09T10:15:23Z",
    "request_id": "req_xyz789",
    "execution_time_ms": 42
  },
  "data": {
    // Actual response data
  }
}
```

### Error Response

**Standard Error:**
```json
{
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "Parametre 'limit' 1-1000 arasında olmalıdır",
    "details": {
      "parameter": "limit",
      "provided": 5000,
      "allowed_range": [1, 1000]
    },
    "request_id": "req_xyz789",
    "timestamp": "2026-02-09T10:15:23Z"
  }
}
```

---

## Error Handling

### HTTP Status Codes

| Kod | Anlamı              | Açıklama                           |
|-----|---------------------|------------------------------------|
| 200 | OK                  | Başarılı                           |
| 201 | Created             | Kaynak oluşturuldu                 |
| 202 | Accepted            | İşlem sıraya alındı (export)       |
| 204 | No Content          | Başarılı silme                     |
| 400 | Bad Request         | Geçersiz parametre                 |
| 401 | Unauthorized        | API key geçersiz/eksik             |
| 403 | Forbidden           | Erişim izni yok                    |
| 404 | Not Found           | Kaynak bulunamadı                  |
| 429 | Too Many Requests   | Rate limit aşıldı                  |
| 500 | Internal Error      | Sunucu hatası                      |
| 503 | Service Unavailable | Bakım modu                         |

### Error Codes

| Code                    | HTTP | Açıklama                          |
|-------------------------|------|-----------------------------------|
| `INVALID_API_KEY`       | 401  | API key hatalı veya expired       |
| `MISSING_API_KEY`       | 401  | Authorization header eksik        |
| `RATE_LIMIT_EXCEEDED`   | 429  | İstek limiti aşıldı               |
| `QUOTA_EXCEEDED`        | 429  | Export kotası doldu               |
| `INVALID_PARAMETER`     | 400  | Parametre formatı hatalı          |
| `MISSING_PARAMETER`     | 400  | Zorunlu parametre eksik           |
| `RESOURCE_NOT_FOUND`    | 404  | Koleksiyon/export bulunamadı      |
| `PERMISSION_DENIED`     | 403  | Yetki yetersiz                    |
| `COLLECTION_NOT_FOUND`  | 404  | Koleksiyon ID geçersiz            |
| `EXPORT_EXPIRED`        | 410  | Export süresi dolmuş (30 gün)     |
| `INTERNAL_ERROR`        | 500  | Beklenmeyen sunucu hatası         |

### Error Handling Example

**Python:**
```python
import requests

def safe_api_call(url, headers):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("API key geçersiz!")
        elif e.response.status_code == 429:
            retry_after = e.response.headers.get('Retry-After', 60)
            print(f"Rate limit! {retry_after} saniye bekleyin.")
        elif e.response.status_code == 404:
            print("Kaynak bulunamadı")
        else:
            error_data = e.response.json()
            print(f"Hata: {error_data['error']['message']}")
        
        return None
    
    except requests.exceptions.ConnectionError:
        print("Bağlantı hatası. İnternet bağlantınızı kontrol edin.")
        return None
```

---

## Code Examples

### Python

**Setup:**
```bash
pip install requests python-dotenv
```

**Environment (.env):**
```
OCRCHESTRA_API_KEY=ocrch_1234567890abcdef
OCRCHESTRA_API_BASE=https://api.ocrchestra.tr/v1
```

**Example Code:**
```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('OCRCHESTRA_API_KEY')
BASE_URL = os.getenv('OCRCHESTRA_API_BASE')

class OCRchestraAPI:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def search(self, query, limit=100, context=20):
        """Korpusta arama yap"""
        params = {
            'q': query,
            'limit': limit,
            'context': context
        }
        response = requests.get(
            f'{self.base_url}/search',
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def frequency_analysis(self, collection_id=None, min_freq=5):
        """Frekans analizi"""
        payload = {
            'collection_id': collection_id,
            'options': {
                'min_frequency': min_freq,
                'max_results': 100
            }
        }
        response = requests.post(
            f'{self.base_url}/analysis/frequency',
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def create_export(self, export_type, format='csv', query=None):
        """Export oluştur"""
        payload = {
            'type': export_type,
            'format': format,
            'search_query': {'q': query} if query else None
        }
        response = requests.post(
            f'{self.base_url}/export',
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def download_export(self, export_id, filename):
        """Export dosyasını indir"""
        response = requests.get(
            f'{self.base_url}/export/{export_id}/download',
            headers=self.headers,
            stream=True
        )
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return filename

# Kullanım
api = OCRchestraAPI(API_KEY, BASE_URL)

# Arama
results = api.search('dilbilim', limit=10)
print(f"Toplam sonuç: {results['metadata']['total_matches']}")
for match in results['results']:
    print(f"{match['left_context']} **{match['keyword']}** {match['right_context']}")

# Frekans analizi
freq_data = api.frequency_analysis(min_freq=10)
print("\nEn sık kelimeler:")
for item in freq_data['frequencies'][:10]:
    print(f"{item['word']}: {item['count']}")

# Export oluştur ve indir
export_job = api.create_export('concordance', 'csv', 'dilbilim')
export_id = export_job['export_id']
print(f"\nExport oluşturuldu: {export_id}")

# 30 saniye bekle ve indir
import time
time.sleep(30)
api.download_export(export_id, 'dilbilim_results.csv')
print("Export indirildi: dilbilim_results.csv")
```

### JavaScript (Node.js)

**Setup:**
```bash
npm install axios dotenv
```

**Example:**
```javascript
const axios = require('axios');
require('dotenv').config();

const API_KEY = process.env.OCRCHESTRA_API_KEY;
const BASE_URL = process.env.OCRCHESTRA_API_BASE;

class OCRchestraAPI {
  constructor(apiKey, baseUrl) {
    this.client = axios.create({
      baseURL: baseUrl,
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      }
    });
  }

  async search(query, options = {}) {
    const params = {
      q: query,
      limit: options.limit || 100,
      context: options.context || 20
    };

    try {
      const response = await this.client.get('/search', { params });
      return response.data;
    } catch (error) {
      console.error('Search error:', error.response?.data || error.message);
      throw error;
    }
  }

  async frequencyAnalysis(collectionId = null, minFreq = 5) {
    const payload = {
      collection_id: collectionId,
      options: {
        min_frequency: minFreq,
        max_results: 100
      }
    };

    try {
      const response = await this.client.post('/analysis/frequency', payload);
      return response.data;
    } catch (error) {
      console.error('Frequency analysis error:', error.response?.data || error.message);
      throw error;
    }
  }

  async createExport(type, format = 'csv', query = null) {
    const payload = {
      type: type,
      format: format,
      search_query: query ? { q: query } : null
    };

    try {
      const response = await this.client.post('/export', payload);
      return response.data;
    } catch (error) {
      console.error('Export creation error:', error.response?.data || error.message);
      throw error;
    }
  }
}

// Kullanım
(async () => {
  const api = new OCRchestraAPI(API_KEY, BASE_URL);

  // Arama
  const results = await api.search('dilbilim', { limit: 10 });
  console.log(`Toplam sonuç: ${results.metadata.total_matches}`);
  
  results.results.forEach(match => {
    console.log(`${match.left_context} **${match.keyword}** ${match.right_context}`);
  });

  // Frekans analizi
  const freqData = await api.frequencyAnalysis(null, 10);
  console.log('\nEn sık kelimeler:');
  freqData.frequencies.slice(0, 10).forEach(item => {
    console.log(`${item.word}: ${item.count}`);
  });

  // Export
  const exportJob = await api.createExport('concordance', 'csv', 'dilbilim');
  console.log(`\nExport oluşturuldu: ${exportJob.export_id}`);
})();
```

### R

**Setup:**
```R
install.packages(c("httr", "jsonlite"))
```

**Example:**
```R
library(httr)
library(jsonlite)

API_KEY <- Sys.getenv("OCRCHESTRA_API_KEY")
BASE_URL <- "https://api.ocrchestra.tr/v1"

# Arama fonksiyonu
search_corpus <- function(query, limit = 100) {
  response <- GET(
    paste0(BASE_URL, "/search"),
    add_headers(Authorization = paste("Bearer", API_KEY)),
    query = list(q = query, limit = limit)
  )
  
  stop_for_status(response)
  content(response, as = "parsed")
}

# Frekans analizi
frequency_analysis <- function(collection_id = NULL, min_freq = 5) {
  payload <- list(
    collection_id = collection_id,
    options = list(
      min_frequency = min_freq,
      max_results = 100
    )
  )
  
  response <- POST(
    paste0(BASE_URL, "/analysis/frequency"),
    add_headers(
      Authorization = paste("Bearer", API_KEY),
      `Content-Type` = "application/json"
    ),
    body = toJSON(payload, auto_unbox = TRUE),
    encode = "raw"
  )
  
  stop_for_status(response)
  content(response, as = "parsed")
}

# Kullanım
results <- search_corpus("dilbilim", limit = 10)
cat("Toplam sonuç:", results$metadata$total_matches, "\n\n")

for (match in results$results) {
  cat(match$left_context, "**", match$keyword, "**", match$right_context, "\n")
}

# Frekans
freq_data <- frequency_analysis(min_freq = 10)
cat("\nEn sık kelimeler:\n")
freq_df <- do.call(rbind, lapply(freq_data$frequencies[1:10], as.data.frame))
print(freq_df[, c("word", "count")])
```

---

## SDKs

### Official SDKs

**Python SDK:**
```bash
pip install ocrchestra-sdk
```

**GitHub:** [github.com/ocrchestra/python-sdk](https://github.com/ocrchestra/python-sdk)

**Node.js SDK:**
```bash
npm install @ocrchestra/sdk
```

**GitHub:** [github.com/ocrchestra/node-sdk](https://github.com/ocrchestra/node-sdk)

### Community SDKs

- **R:** `oRCHchestra` package (CRAN)
- **Java:** `ocrchestra-java` (Maven Central)
- **Go:** `go-ocrchestra` (GitHub)

---

## Changelog

### v1.0 (Şubat 2026)
- ✨ İlk API release
- 🔍 Search endpoints (basic & advanced)
- 📊 Analysis endpoints (frequency, n-gram, collocation)
- 📥 Export system (CSV, JSON, Excel)
- 🏷️ Collections CRUD
- 👤 User quota & usage tracking
- 🔐 Bearer token authentication
- ⏱️ Rate limiting (100/min, 2000/day)

### Roadmap (v1.1 - Q2 2026)
- 🎯 Webhook support for export completion
- 🔄 Batch processing API
- 📈 Real-time streaming search
- 🌍 Multi-language support
- 🔑 OAuth2 authentication
- 📊 GraphQL endpoint
- 🧪 Sandbox environment improvements

---

## İletişim ve Destek

**API Desteği:**
- E-posta: developer@ocrchestra.tr
- GitHub Issues: [github.com/ocrchestra/api-docs/issues](https://github.com/ocrchestra/api-docs/issues)
- Twitter: @ocrchestra_dev

**Dokümantasyon:**
- API Reference: https://api-docs.ocrchestra.tr
- Examples: https://github.com/ocrchestra/api-examples
- Postman Collection: [Download](https://www.postman.com/ocrchestra/workspace/)

**Topluluk:**
- Discord: discord.gg/ocrchestra
- Stack Overflow: Tag `ocrchestra`

---

**OCRchestra API v1.0**  
*Developer Documentation*  
© 2026 OCRchestra Platform

---

**Lisans:** API kullanımı için Terms of Service geçerlidir.  
**Son Güncelleme:** 9 Şubat 2026
