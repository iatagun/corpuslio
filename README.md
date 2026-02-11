# CorpusLIO

**Modern, API-first Turkish Corpus Infrastructure**  
Supporting CoNLL-U, VRT and scalable corpus serving.

---

## 🧭 Vision

Turkey needs modern corpus infrastructure that scales beyond desktop tools. CorpusLIO addresses three critical gaps:

**1. API-First Architecture**  
NoSketchEngine and CWB were designed for single-user desktop workflows. Modern NLP research requires programmatic access, batch processing, and institutional deployment. CorpusLIO exposes corpus operations through RESTful APIs with authentication, rate limiting, and quota management.

**2. Dependency-Aware Querying**  
Traditional concordancers treat syntax as metadata. CorpusLIO natively understands CoNLL-U dependency trees, enabling queries like "find all subjects of passive verbs" without custom regex patterns.

**3. Public Infrastructure Readiness**  
Most corpus tools assume trusted internal users. CorpusLIO is built for public-facing deployment with GDPR compliance, user management, export watermarking, and audit logging—critical for institutional use.

> **This is infrastructure, not just a search interface.**

---

## 👤 About

**Designed and maintained by İlker Atagün**  
Research focus: Turkish NLP infrastructure & corpus systems

This project emerged from the need for scalable, production-grade corpus tooling in Turkish linguistics research. It combines academic rigor with modern software engineering practices.

---

## ✅ Current Status

### Implemented Features
- ✅ **Corpus Upload & Parsing** — CoNLL-U and VRT validation
- ✅ **CQP Query Engine** — Pattern matching via CWB integration
- ✅ **Concordance Search** — KWIC display with context windows
- ✅ **User Authentication** — OAuth2, JWT tokens, role-based access
- ✅ **Export System** — JSON, CSV formats with watermarking
- ✅ **Rate Limiting** — Per-user query quotas and throttling
- ✅ **RESTful API** — OpenAPI 3.0 documentation
- ✅ **Redis Caching** — Query result caching for performance
- ✅ **Dependency Visualization** — Tree rendering for syntactic structures
- ✅ **GDPR Tools** — Data export, anonymization, deletion workflows

### Planned Features (Roadmap)
- 🔲 **Full CWB Pipeline** — Automated corpus indexing and vertical compilation
- 🔲 **Advanced Dependency Queries** — SQL-like syntax for dependency relations
- 🔲 **Collocation Extraction** — Statistical association measures (t-score, MI)
- 🔲 **N-gram Frequency** — Multi-word unit analysis
- 🔲 **Background Task Queue** — Celery integration for large exports
- 🔲 **Multi-corpus Search** — Federated queries across corpora

**Current maturity:** Alpha (core features working, API stable, production testing ongoing)

---

## 🔬 Academic Use

### Citation

If you use CorpusLIO in academic work, please cite:

```
Atagün, İ. (2026). CorpusLIO: API-First Corpus Infrastructure for Turkish.
GitHub repository: https://github.com/iatagun/corpuslio
```

### Research Statement

This platform is designed for:
- University linguistics departments requiring multi-user corpus access
- NLP researchers needing programmatic query interfaces
- Language technology companies building on annotated data
- Public institutions serving linguistic resources at scale

**Not a toy project.** Built for institutional deployment with authentication, audit trails, and compliance tools.

---

## 🏛 Why Not NoSketchEngine / CWB?

| Limitation | Traditional Tools | CorpusLIO |
|-----------|------------------|-----------|
| **API Access** | Desktop GUI or shell scripts | RESTful API with OpenAPI docs |
| **Multi-user** | Shared server, no quotas | Per-user rate limits, usage tracking |
| **Dependency Queries** | Manual CQP regex patterns | Native CoNLL-U parsing, tree queries |
| **Deployment** | Server admin required | Docker + Django, PaaS-ready |
| **Authentication** | Basic auth or none | OAuth2, JWT, role-based access |
| **Compliance** | No audit logs | GDPR tools, export logs, watermarking |

**CWB is excellent** for corpus indexing. CorpusLIO wraps it with modern web infrastructure and adds features needed for 2026.

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

## 🤝 Contributing

This project welcomes contributions from:
- NLP researchers improving query algorithms
- Frontend developers enhancing the UI
- DevOps engineers optimizing deployment
- Linguists testing with real-world corpora

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

For issues, questions, or institutional deployment inquiries, please open an issue on GitHub.

