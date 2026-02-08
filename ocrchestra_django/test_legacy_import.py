"""Test CorpusService import after fixing relative import issue."""

import os
import sys
import django

# Mock groq if not available
try:
    import groq
except ImportError:
    from types import ModuleType
    groq = ModuleType('groq')
    sys.modules['groq'] = groq

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ocrchestra_django.settings')
django.setup()

print("✅ Django setup complete")

# Test imports
try:
    from corpus.services import CorpusService
    print(f"✅ CorpusService imported: {CorpusService}")
    
    from corpus.services import ExportService
    print(f"✅ ExportService imported: {ExportService}")
    
    print("\n✅ All imports working after fixing relative import!")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
