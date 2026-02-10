"""
WSGI entry for production (PythonAnywhere).

This sets the `DJANGO_SETTINGS_MODULE` to the production settings file.
Configure your PythonAnywhere web app to point to this WSGI file.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'corpuslio_django.settings_prod')

application = get_wsgi_application()
