# CorpusLIO

**Modern, API-first Turkish Corpus Infrastructure**  
Supporting CoNLL-U, VRT and scalable corpus serving.

---

## What is CorpusLIO?

A production-ready linguistic corpus platform designed for Turkish language researchers, NLP engineers, and linguists. Upload annotated corpora, run advanced queries, analyze dependencies, and export results—all through a RESTful API or web interface.

**Built for scale:** Handles millions of tokens with CWB integration, Redis caching, and Celery task queues.

---

## ✨ Features

- **📊 Multiple Format Support** — Import CoNLL-U and VRT files with automatic validation
- **🔍 Advanced Search** — CQP queries, concordance, collocations, n-grams, frequency analysis
- **🌳 Dependency Parsing** — Visualize and query syntactic structures
- **🔐 User Management** — Role-based access, query quotas, GDPR-compliant data handling
- **📡 RESTful API** — OpenAPI/Swagger documentation with rate limiting and OAuth2
- **⚡ Performance** — Redis caching, background tasks with Celery, database query optimization
- **🌐 Internationalization** — Multi-language UI (Turkish/English) with Django i18n
- **📤 Export Options** — JSON, CSV, CoNLL-U formats with watermarking and quota tracking

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Redis (for caching)
- PostgreSQL (recommended for production)

### Installation

```powershell
# Clone the repository
git clone https://github.com/iatagun/corpuslio.git
cd corpuslio

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r corpuslio_django/requirements.txt

# Set environment
$env:DJANGO_SETTINGS_MODULE='corpuslio_django.settings'

# Initialize database
cd corpuslio_django
python manage.py migrate
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

Visit `http://127.0.0.1:8000` to access the platform.

---

## 🛠 Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Django 5.x, Django REST Framework |
| **Database** | PostgreSQL (production), SQLite (dev) |
| **Task Queue** | Celery + Redis |
| **Caching** | Redis |
| **Corpus Engine** | CWB (Corpus Workbench) integration |
| **API Docs** | drf-spectacular (OpenAPI 3.0) |
| **Authentication** | OAuth2, JWT tokens |
| **Deployment** | Docker, PythonAnywhere, WhiteNoise for static files |

---

## 📚 API Documentation

Interactive API documentation available at:
- **Swagger UI:** `/tr/api/schema/swagger-ui/`
- **ReDoc:** `/tr/api/schema/redoc/`
- **OpenAPI Schema:** `/tr/api/schema/` (YAML/JSON)

### Example API Request

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/tr/api/search/?q=bakanlık&corpus=milliyet"
```

---

## 🌍 Production Deployment

### Environment Variables

```bash
export DJANGO_SETTINGS_MODULE=corpuslio_django.settings_prod
export DATABASE_URL=postgresql://user:pass@localhost/corpuslio
export REDIS_URL=redis://localhost:6379/0
export SECRET_KEY=your-secret-key
export ALLOWED_HOSTS=yourdomain.com
```

### Docker Deployment

```bash
docker-compose up -d
```

### Static Files

```bash
python manage.py collectstatic --noinput
```

For PythonAnywhere, Heroku, or similar platforms, use `wsgi_prod.py` as the WSGI entry point.

---

## 🧪 Running Tests

```bash
python manage.py test corpus
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is available at [github.com/iatagun/corpuslio](https://github.com/iatagun/corpuslio).

---

## 📞 Support

For issues, questions, or contributions, please open an issue on GitHub.

