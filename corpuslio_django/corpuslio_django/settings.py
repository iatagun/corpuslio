"""
Django settings for corpuslio_django project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import mimetypes
# Force CSS content type (Fix for Windows registry issues)
mimetypes.add_type("text/css", ".css", True)

# Additional fix for Windows 10/11 where registry entry might be missing/corrupt
if os.name == 'nt':
    import mimetypes
    mimetypes.init()
    if '.css' not in mimetypes.types_map or mimetypes.types_map['.css'] != 'text/css':
        mimetypes.types_map['.css'] = 'text/css'

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-1w#1kzyj_d0pbw#54nbkj$qk-)df_y$4+^2)=mp+4n6wn(@7zl')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# CSRF Settings (Task 11.11)
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = False  # JavaScript needs to read CSRF token


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',
    'drf_spectacular',
    # Authentication
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    # Google provider temporarily disabled during troubleshooting
    # 'allauth.socialaccount.providers.google',
    
    # Local apps
    'corpus',
    'api',
]

# Site framework configuration
SITE_ID = 1

MIDDLEWARE = [
    # Security middleware (Week 10)
    'corpus.security_middleware.SecurityHeadersMiddleware',
    'corpus.security_middleware.ContentSecurityPolicyMiddleware',
    'corpus.security_middleware.RequestValidationMiddleware',
    
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # i18n support
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Session security (Week 10)
    'corpus.security_middleware.SessionSecurityMiddleware',
    
    # Custom middleware for query logging and export tracking
    'corpus.middleware.QueryLogMiddleware',
    'corpus.middleware.ExportLogMiddleware',
]

ROOT_URLCONF = 'corpuslio_django.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',  # i18n support
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
            ],
        },
    },
]

WSGI_APPLICATION = 'corpuslio_django.wsgi.application'

import dj_database_url

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# Default: SQLite (for local dev without Docker)
# Production: PostgreSQL (via DATABASE_URL env var)
DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        conn_max_age=600
    )
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
}

# drf-spectacular settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'CorpusLIO API',
    'DESCRIPTION': 'OpenAPI schema for CorpusLIO',
    'VERSION': '1.0.0',
}

# Logging (minimal) to avoid setup-time errors
LOGGING_CONFIG = None
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
}

# Email Configuration (Task 11.2)
# =================================

# Use environment variables for email backend configuration
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.sendgrid.net')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'apikey')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

# Email sender configuration
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'CorpusLIO <noreply@corpuslio.com>')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Email template configuration
EMAIL_SUBJECT_PREFIX = '[CorpusLIO] '

# Email timeout (prevent hanging)
EMAIL_TIMEOUT = 10

# Django Ratelimit Configuration (Task 11.10)
RATELIMIT_VIEW = 'corpus.views.ratelimit_handler'
RATELIMIT_ENABLE = os.getenv('RATELIMIT_ENABLE', 'False') == 'True'  # Enable in production via .env

# Celery Configuration
# ====================
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Istanbul'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes max per task

# Celery Beat Schedule (Periodic tasks)
CELERY_BEAT_SCHEDULE = {
    'cleanup-old-exports': {
        'task': 'corpus.cleanup_old_exports',
        'schedule': 86400.0,  # Daily (24 hours)
    },
    'cleanup-old-tasks': {
        'task': 'corpus.tasks.cleanup_old_tasks',
        'schedule': 86400.0,  # Daily
    },
}

# (Remaining settings unchanged - project-local settings preserved)
