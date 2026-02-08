"""
Quick test to verify ExportService can be imported.
"""

import sys
import os

# Add Django project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing ExportService import...")

try:
    from corpus.services import ExportService
    print("✅ SUCCESS: ExportService imported successfully!")
    print(f"   Location: {ExportService.__module__}")
    print(f"   Methods available:")
    for method in dir(ExportService):
        if not method.startswith('_') and callable(getattr(ExportService, method)):
            print(f"     - {method}()")
except ImportError as e:
    print(f"✗ FAILED: {e}")
    sys.exit(1)

print("\nTesting openpyxl import...")
try:
    import openpyxl
    print(f"✅ SUCCESS: openpyxl version {openpyxl.__version__}")
except ImportError as e:
    print(f"✗ FAILED: {e}")
    sys.exit(1)

print("\nAll import tests passed! Export system is ready.")
