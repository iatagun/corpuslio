
import os
import django
from django.conf import settings
from django.urls import reverse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ocrchestra_django.settings')
django.setup()

try:
    url = reverse('corpus:analysis', args=[1])
    print(f"Success: {url}")
except Exception as e:
    print(f"Error: {e}")
