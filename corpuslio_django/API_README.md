# OCRchestra Corpus API Documentation

**Version:** 1.0.0  
**Base URL:** `http://localhost:8000/api/v1/`  
**Authentication:** API Key or Session

---

## 🚀 Quick Start

### 1. Get an API Key

Log in to the platform and create an API key:

```python
# Visit: /api/v1/keys/
# Or use Django admin panel
```

### 2. Make Your First Request

```bash
# Using cURL
curl -H "Authorization: Api-Key YOUR_API_KEY_HERE" \
  http://localhost:8000/api/v1/documents/

# Using query parameter
curl http://localhost:8000/api/v1/documents/?api_key=YOUR_API_KEY_HERE
```

### 3. Explore with Swagger UI

Visit: `http://localhost:8000/api/docs/`

---

## 📚 API Endpoints

### Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/documents/` | List all documents (filterable) |
| GET | `/documents/{id}/` | Get document details |
| GET | `/documents/search/` | Full-text concordance search |
| GET | `/documents/{id}/frequency/` | Word frequency list for document |

**Filters:**
- `genre`, `author`, `year`, `language`
- `text_type`, `license`, `collection`
- `privacy_status`

**Example:**
```bash
# Get all documents from 2024
GET /api/v1/documents/?year=2024

# Filter by genre and collection
GET /api/v1/documents/?genre=Academic&collection=MEB
```

### Search (Concordance)

```bash
GET /api/v1/documents/search/?q=derlem&context=5&limit=100
```

**Parameters:**
- `q` (required): Search query
- `context` (default: 5): Number of context words
- `limit` (default: 100, max: 1000): Max results

**Response:**
```json
{
  "query": "derlem",
  "total_results": 42,
  "results": [
    {
      "document_id": 10,
      "document_title": "Türkçe Derlemler",
      "left_context": "ulusal dilbilim konferansında",
      "keyword": "derlem",
      "right_context": "çalışmaları sunuldu ve",
      "position": 15,
      "sentence": "ulusal dilbilim konferansında derlem çalışmaları sunuldu ve"
    }
  ]
}
```

### Frequency Lists

```bash
# Document-specific frequency
GET /api/v1/documents/10/frequency/?limit=100&min_freq=2

# Global corpus frequency
GET /api/v1/frequency/?genre=Academic&limit=500&min_freq=5
```

**Response:**
```json
{
  "document_id": 10,
  "document_title": "Türkçe Derlemler",
  "total_words": 5432,
  "unique_words": 100,
  "frequencies": [
    {
      "word": "derlem",
      "frequency": 45,
      "relative_frequency": 8283.12
    }
  ]
}
```

### Tags

```bash
GET /api/v1/tags/
```

### API Keys Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/keys/` | List your API keys |
| POST | `/keys/` | Create new API key |
| GET | `/keys/{id}/` | Get API key details |
| PUT/PATCH | `/keys/{id}/` | Update API key |
| DELETE | `/keys/{id}/` | Delete API key |
| POST | `/keys/{id}/regenerate/` | Regenerate API key |

---

## 🔐 Authentication

### API Key Authentication

**Header:**
```
Authorization: Api-Key YOUR_API_KEY_HERE
```

**Query Parameter:**
```
?api_key=YOUR_API_KEY_HERE
```

### Session Authentication

If you're logged in to the Django web interface, you can use the browsable API directly.

---

## ⚡ Rate Limiting

### Tiers

| Tier | Requests/Hour | Searches/Hour | Exports/Day |
|------|---------------|---------------|-------------|
| **Free** | 60 | 30 | 10 |
| **Standard** | 600 | 300 | 50 |
| **Premium** | 3,000 | 1,200 | 200 |
| **Unlimited** | 10,000 | 6,000 | 1,000 |

### Quotas

- **Daily Quota:** API keys have daily request limits based on tier
- **Burst Protection:** Max 10 requests per minute to prevent rapid-fire attacks
- **Anonymous Users:** 10 requests per day (no API key)

### Headers

Check remaining quota in response headers:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1675872000
```

---

## 📖 OpenAPI Documentation

### Swagger UI (Interactive)

**URL:** `/api/docs/`

Features:
- Try API endpoints directly in browser
- View request/response schemas
- Generate code snippets

### ReDoc (Documentation)

**URL:** `/api/redoc/`

Clean, readable API documentation.

### OpenAPI Schema (JSON)

**URL:** `/api/schema/`

Download raw OpenAPI 3.0 schema for code generation.

---

## 🔍 Filtering & Search

### Query Parameters

- **Search:** `search=query`
- **Ordering:** `ordering=field` or `ordering=-field` (descending)
- **Pagination:** `page=2&page_size=50`

**Example:**
```bash
GET /api/v1/documents/?search=linguistics&ordering=-year&page_size=20
```

---

## 📊 Response Format

### Success Response

```json
{
  "count": 150,
  "next": "http://localhost:8000/api/v1/documents/?page=2",
  "previous": null,
  "results": [...]
}
```

### Error Response

```json
{
  "detail": "Invalid API key",
  "status_code": 401
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (invalid parameters) |
| 401 | Unauthorized (invalid/missing API key) |
| 403 | Forbidden (quota exceeded, permission denied) |
| 404 | Not Found |
| 429 | Too Many Requests (rate limited) |
| 500 | Internal Server Error |

---

##  Code Examples

### Python

```python
import requests

API_KEY = 'your_api_key_here'
BASE_URL = 'http://localhost:8000/api/v1/'

# Set up authentication
headers = {
    'Authorization': f'Api-Key {API_KEY}'
}

# List documents
response = requests.get(f'{BASE_URL}documents/', headers=headers)
documents = response.json()['results']

# Search concordance
params = {
    'q': 'derlem',
    'context': 5,
    'limit': 50
}
response = requests.get(f'{BASE_URL}documents/search/', headers=headers, params=params)
results = response.json()

print(f"Found {results['total_results']} matches")
for result in results['results']:
    print(f"{result['document_title']}: {result['sentence']}")

# Get frequency list
response = requests.get(f'{BASE_URL}documents/10/frequency/', headers=headers)
frequencies = response.json()['frequencies']

for item in frequencies[:20]:
    print(f"{item['word']}: {item['frequency']}")
```

### JavaScript (Fetch)

```javascript
const API_KEY = 'your_api_key_here';
const BASE_URL = 'http://localhost:8000/api/v1/';

// Fetch documents
async function getDocuments() {
  const response = await fetch(`${BASE_URL}documents/`, {
    headers: {
      'Authorization': `Api-Key ${API_KEY}`
    }
  });
  
  const data = await response.json();
  return data.results;
}

// Search concordance
async function searchConcordance(query) {
  const params = new URLSearchParams({
    q: query,
    context: 5,
    limit: 100
  });
  
  const response = await fetch(`${BASE_URL}documents/search/?${params}`, {
    headers: {
      'Authorization': `Api-Key ${API_KEY}`
    }
  });
  
  return await response.json();
}

// Use the functions
getDocuments().then(docs => console.log('Documents:', docs));
searchConcordance('derlem').then(results => console.log('Results:', results));
```

### cURL

```bash
# List documents
curl -H "Authorization: Api-Key YOUR_API_KEY" \
  "http://localhost:8000/api/v1/documents/"

# Search with filters
curl -H "Authorization: Api-Key YOUR_API_KEY" \
  "http://localhost:8000/api/v1/documents/?genre=Academic&year=2024"

# Concordance search
curl -H "Authorization: Api-Key YOUR_API_KEY" \
  "http://localhost:8000/api/v1/documents/search/?q=dilbilim&context=5"

# Frequency list
curl -H "Authorization: Api-Key YOUR_API_KEY" \
  "http://localhost:8000/api/v1/documents/10/frequency/?limit=50"
```

---

## 🛡️ Security Best Practices

1. **Keep API Keys Secret**
   - Never commit API keys to version control
   - Use environment variables: `API_KEY=os.getenv('CORPUS_API_KEY')`

2. **Use HTTPS in Production**
   - API keys transmitted in plain text over HTTP can be intercepted

3. **Rotate Keys Regularly**
   - Regenerate API keys periodically
   - Delete unused/old keys

4. **Restrict by IP (Optional)**
   - Set `allowed_ips` in API key settings

5. **Monitor Usage**
   - Check request counts and patterns
   - Watch for suspicious activity

---

## 🆘 Troubleshooting

### "Invalid API key"

- Check if API key is active
- Verify expiration date
- Ensure correct format: `Authorization: Api-Key YOUR_KEY`

### "Quota exceeded"

- Check your tier limits
- Wait for daily/hourly reset
- Upgrade to higher tier

### "Rate limited" (429)

- Slow down request rate
- Implement retry logic with exponential backoff
- Upgrade tier for higher limits

### Empty results

- Check privacy_status filters
- Verify document access permissions
- Try broader search terms

---

##  Support

- **Documentation:** `/api/docs/`
- **GitHub Issues:** [OCRchestra Repository](#)
- **Email:** support@ocrchestra.org

---

**Happy Coding! 🚀**
