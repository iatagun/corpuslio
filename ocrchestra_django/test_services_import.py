"""
Test corpus.services imports using Django setup.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ocrchestra_django.settings')

# Disable GROQ imports temporarily
import importlib.util
spec = importlib.util.find_spec('groq')
if spec is None:
    # Mock groq module
    from unittest.mock import MagicMock
    sys.modules['groq'] = MagicMock()

try:
    django.setup()
    print("Django setup complete")
except Exception as e:
    print(f"⚠️  Django setup partially failed: {e}")
    print("Continuing with import test...")

# Now test imports
try:
    from corpus.services import CorpusService, ExportService
    print("\n✅ SUCCESS: Both services imported!")
    print(f"   - CorpusService: {CorpusService}")
    print(f"   - ExportService: {ExportService}")
    print("\n✅ All imports working correctly!")
    sys.exit(0)
except ImportError as e:
    print(f"\n✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
