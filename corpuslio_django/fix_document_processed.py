"""
Fix processed status for sample CoNLL-U document.
"""

import os
import sys
import django

# Setup paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'corpuslio_django.settings')
django.setup()

from corpus.models import Document

# Update document 14
try:
    doc = Document.objects.get(id=14)
    doc.processed = True
    doc.save()
    print(f"✅ Document {doc.id} ({doc.filename}) marked as processed")
except Document.DoesNotExist:
    print("❌ Document with ID 14 not found")
