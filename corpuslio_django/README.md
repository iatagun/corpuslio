# CorpusLIO Django

Modern Django-based Turkish corpus platform with AI-powered linguistic analysis.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and add your keys:

```bash
GROQ_API_KEY=your_groq_api_key_here
DJANGO_SECRET_KEY=your_secret_key
```

### 3. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser (Admin)

```bash
python manage.py createsuperuser
```

### 5. Start Development Server

```bash
python manage.py runserver
```

Visit: **http://localhost:8000**

## 🔥 Features

- ✅ **Modern Dark Theme** with glassmorphism effects
- ✅ **Document Upload** (PDF, DOCX, TXT, Images)
- ✅ **AI-Powered Analysis** via Groq API (POS tagging, lemmatization)
- ✅ **Async Processing** with Celery
- ✅ **KWIC Concordance** search
- ✅ **REST API** with Django REST Framework
- ✅ **Export** to VRT, JSON, CSV, CoNLL-U formats

## 📁 Project Structure

```
ocrchestra_django/
├── manage.py
├── ocrchestra_django/          # Django settings
│   ├── settings.py
│   ├── urls.py
│   └── celery.py
├── corpus/                      # Main app
│   ├── models.py               # Document, Content, Analysis
│   ├── views.py                # Library, Upload, Analysis views
│   ├── forms.py
│   ├── services.py             # Business logic wrapper
│   └── tasks.py                # Celery async tasks
├── api/                         # REST API
│   ├── views.py
│   └── urls.py
├── templates/corpus/            # HTML templates
│   ├── base.html
│   ├── library.html
│   ├── upload.html
│   └── statistics.html
├── static/
│   ├── css/styles.css          # Modern dark theme
│   └── js/app.js
└── media/                       # Uploaded files
```

## 🎨 Design

Modern dark theme ported from Streamlit:
- **Colors**: `#0f172a`, `#1e293b`, `#6366f1`, `#8b5cf6`
- **Fonts**: Inter, JetBrains Mono
- **Effects**: Glassmorphism, gradients, smooth animations

## 📡 API Endpoints

```
GET  /api/documents/             # List documents
POST /api/search/                # Search corpus
GET  /api/stats/{doc_id}/        # Get statistics
GET  /api/export/{doc_id}/       # Export document
```

## 🐳 Docker (Optional)

Coming soon: Docker Compose with Celery, Redis, and Nginx.

## 🛠️ Technology Stack

- **Backend**: Django 5.0
- **API**: Django REST Framework
- **Async**: Celery + Redis
- **Database**: SQLite (dev) / PostgreSQL (production)
- **NLP**: Groq API (Turkish language model)
- **Frontend**: Vanilla HTML/CSS/JS

## 📝 License

MIT
