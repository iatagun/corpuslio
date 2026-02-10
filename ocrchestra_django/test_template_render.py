
import os
import django
from django.conf import settings
from django.template.loader import render_to_string

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ocrchestra_django.settings')
django.setup()

try:
    rendered = render_to_string('test_reverse.html')
    print(f"Success: {rendered.strip()}")
except Exception as e:
    print(f"Error: {e}")
