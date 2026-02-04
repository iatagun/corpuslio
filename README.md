# OCRchestra - Turkish Corpus Platform

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
python manage.py createsuperuser

# Run server
python manage.py runserver
```

Visit: **http://localhost:8000**

## 📁 Project Structure

```
OCRchestra/
├── ocrchestra_django/        # Django web application
│   ├── manage.py
│   ├── corpus/               # Main app
│   ├── api/                  # REST API
│   ├── templates/            # HTML templates
│   └── static/               # CSS, JS
│
├── ocrchestra/               # Core NLP modules (shared)
│   ├── orchestrator.py
│   ├── groq_client.py
│   ├── search_engine.py
│   └── ...
│
├── scripts/                  # Utility scripts
├── tests/                    # Tests
└── README.md                 # This file
```

## 🎨 Features

- ✅ Modern dark theme with glassmorphism
- ✅ Document upload (PDF, DOCX, TXT, images)
- ✅ AI-powered analysis (Groq API)
- ✅ Async processing (Celery)
- ✅ KWIC concordance search
- ✅ REST API
- ✅ Export to VRT, JSON, CSV, CoNLL-U

## 📖 Documentation

See [`ocrchestra_django/README.md`](ocrchestra_django/README.md) for detailed setup instructions.

## 🛠️ Technology Stack

- **Backend**: Django 5.0
- **API**: Django REST Framework
- **Async**: Celery + Redis
- **NLP**: Groq API
- **Database**: SQLite (dev) / PostgreSQL (prod)

## 📝 License

MIT
