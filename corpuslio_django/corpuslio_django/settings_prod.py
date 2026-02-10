"""Production settings overrides for PythonAnywhere deployment.

This file imports the base settings and applies safe defaults for
production. Sensitive values are read from environment variables.
"""
from .settings import *  # noqa: F401,F403
import os
from dj_database_url import config as db_config

# Security
DEBUG = False
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', SECRET_KEY)

# Hosts - set via environment variable on PythonAnywhere
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'yourusername.pythonanywhere.com').split(',')

# Database: use DATABASE_URL env var if present
DATABASES = {
    'default': db_config(default=os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR / "db.sqlite3"}'))
}

# Static files - already defined in base settings; ensure collectstatic runs

# WhiteNoise for serving static files (optional on PythonAnywhere)
MIDDLEWARE.insert(0, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Security headers (adjust as needed)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Disable debug toolbar or other dev-only apps if present
INSTALLED_APPS = [a for a in INSTALLED_APPS if not a.startswith('debug_toolbar')]
