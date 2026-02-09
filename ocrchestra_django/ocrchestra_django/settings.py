"""
Django settings for ocrchestra_django project.
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
    'allauth.socialaccount.providers.google',
    
    # Local apps
    'corpus',
    'api',
]

MIDDLEWARE = [
    # Security middleware (Week 10)
    'corpus.security_middleware.SecurityHeadersMiddleware',
    'corpus.security_middleware.ContentSecurityPolicyMiddleware',
    'corpus.security_middleware.RequestValidationMiddleware',
    
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
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

ROOT_URLCONF = 'ocrchestra_django.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
            ],
        },
    },
]

WSGI_APPLICATION = 'ocrchestra_django.wsgi.application'


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


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Authentication settings
LOGIN_URL = 'corpus:login'
LOGIN_REDIRECT_URL = 'corpus:home'
LOGOUT_REDIRECT_URL = 'corpus:login'

# django-allauth settings
SITE_ID = int(os.getenv('DJANGO_SITE_ID', '1'))

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# allauth behavior
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_AUTHENTICATION_METHOD = 'username'
ACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    }
}

# Note: You must install `django-allauth` (pip install django-allauth)
# and configure a Google OAuth2 app in Google Cloud Console.
# Create a SocialApp in Django admin (Sites -> Social applications) with
# the client id/secret and add the site (SITE_ID).


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'tr'

TIME_ZONE = 'Europe/Istanbul'

USE_I18N = True

USE_TZ = True


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
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    
    # Authentication (Week 7)
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'api.authentication.APIKeyAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    
    # Permissions
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    
    # Throttling (Week 7)
    'DEFAULT_THROTTLE_CLASSES': [
        'api.throttling.APIKeyRateThrottle',
        'api.throttling.BurstRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon_api': '10/day',
        'burst': '10/min',
        'search': '50/hour',
        'export': '20/day',
    },
    
    # Filtering
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# DRF Spectacular settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'OCRchestra Corpus API',
    'DESCRIPTION': 'REST API for Turkish National Corpus Platform - VRT, CoNLL-U, and linguistic analysis',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': r'/api/v[0-9]',
}


# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Istanbul'
CELERY_TASK_ALWAYS_EAGER = True  # Run tasks synchronously in development (no Redis needed)
CELERY_TASK_EAGER_PROPAGATES = True

# Celery Beat Schedule (Periodic Tasks)
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # GDPR/KVKK Data Retention Tasks
    'cleanup-expired-data-exports': {
        'task': 'corpus.tasks.cleanup_expired_data_exports',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        'options': {'description': 'Delete expired data export files (30-day retention)'}
    },
    'process-pending-deletions': {
        'task': 'corpus.tasks.process_pending_deletions',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
        'options': {'description': 'Process account deletions past grace period (7 days)'}
    },
    'cleanup-inactive-accounts': {
        'task': 'corpus.tasks.cleanup_inactive_accounts',
        'schedule': crontab(day_of_month=1, hour=4, minute=0),  # 1st of month at 4 AM
        'options': {'description': 'Notify inactive accounts (2+ years)'}
    },
    'cleanup-old-tasks': {
        'task': 'corpus.tasks.cleanup_old_tasks',
        'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
        'options': {'description': 'Clean up old processing tasks (7 days)'}
    },
}


# OCRchestra specific settings
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50 MB

# Allowed file extensions
ALLOWED_DOCUMENT_EXTENSIONS = ['.pdf', '.docx', '.txt', '.png', '.jpg', '.jpeg']

# Google OAuth credentials (loaded from environment)
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')


# ============================================================
# RATE LIMITING CONFIGURATION (django-ratelimit)
# ============================================================

# Enable rate limiting globally
RATELIMIT_ENABLE = True

# Use default cache for rate limiting
RATELIMIT_USE_CACHE = 'default'

# Custom 429 error handler
RATELIMIT_VIEW = 'corpus.views.rate_limit_exceeded'

# Cache configuration for rate limiting
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'ocrchestra-ratelimit',
    }
}

# ============================================================
# LOGGING CONFIGURATION
# ============================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'corpus.middleware': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}


# ============================================================
# SECURITY HARDENING (Week 10)
# ============================================================

# CSRF Protection
CSRF_COOKIE_SECURE = not DEBUG  # Use secure cookies in production
CSRF_COOKIE_HTTPONLY = True  # Prevent JavaScript access to CSRF cookie
CSRF_COOKIE_SAMESITE = 'Strict'  # Prevent CSRF in cross-site requests
CSRF_USE_SESSIONS = False  # Use cookie-based CSRF (more secure than session)
CSRF_FAILURE_VIEW = 'corpus.views.csrf_failure'  # Custom CSRF error page

# Session Security
SESSION_COOKIE_SECURE = not DEBUG  # Use secure cookies in production
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookie
SESSION_COOKIE_SAMESITE = 'Strict'  # Prevent session hijacking in cross-site requests
SESSION_COOKIE_AGE = 3600  # 1 hour session timeout
SESSION_SAVE_EVERY_REQUEST = True  # Update session on every request
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Keep session for SESSION_COOKIE_AGE

# Security Headers (enforced by middleware)
SECURE_CONTENT_TYPE_NOSNIFF = True  # X-Content-Type-Options: nosniff
SECURE_BROWSER_XSS_FILTER = True  # X-XSS-Protection: 1; mode=block
X_FRAME_OPTIONS = 'DENY'  # Prevent clickjacking

# HTTPS/SSL (production only)
if not DEBUG:
    SECURE_SSL_REDIRECT = True  # Redirect HTTP to HTTPS
    SECURE_HSTS_SECONDS = 31536000  # 1 year HSTS
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Password Hashing (use Argon2 for better security)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',  # Most secure
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

# Host Header Validation
ALLOWED_HOSTS = ['*'] if DEBUG else [
    'ocrchestra.example.com',
    'localhost',
    '127.0.0.1',
]

# Admin Security
ADMIN_URL = os.getenv('ADMIN_URL', 'admin/')  # Customize admin URL

# File Upload Security (already configured above, but grouped here)
# FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50 MB
# DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50 MB
# ALLOWED_DOCUMENT_EXTENSIONS = ['.pdf', '.docx', '.txt', '.png', '.jpg', '.jpeg']

# SQL Injection Prevention (Django ORM handles this automatically)
# Never use .raw() or .extra() with user input
# Always use parameterized queries

# XSS Prevention
# Templates use {% autoescape on %} by default
# Always escape user input in templates
# Use |safe filter ONLY for trusted content

# Input Validation
# All user inputs validated using corpus.validators module
# File uploads validated for type, size, and content
# Query inputs sanitized to prevent injection attacks
