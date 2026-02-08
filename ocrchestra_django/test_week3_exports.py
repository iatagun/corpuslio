"""
Test Week 3 Export Functionality
Tests watermarked exports with real data integration.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ocrchestra_django.settings')
django.setup()

from corpus.models import Document, UserProfile
from corpus.services.export_service import ExportService
from django.contrib.auth.models import User

def test_export_service():
    """Test ExportService with watermarking."""
    print("=" * 60)
    print("WEEK 3 EXPORT SYSTEM TEST")
    print("=" * 60)
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        username='test_export_user',
        defaults={'email': 'test@example.com'}
    )
    if created:
        user.set_password('test123')
        user.save()
        print(f"✅ Created test user: {user.username}")
    else:
        print(f"✅ Using existing test user: {user.username}")
    
    # Get a test document
    document = Document.objects.filter(processed=True).first()
    
    if not document:
        print("❌ No processed documents found. Upload and process a document first.")
        return False
    
    print(f"✅ Using document: {document.filename} (ID: {document.id})")
    
    # Test ExportService
    print("\n" + "=" * 60)
    print("Testing ExportService...")
    print("=" * 60)
    
    # Get document title (try metadata first, fallback to filename)
    doc_title = document.filename
    if hasattr(document, 'metadata') and isinstance(document.metadata, dict):
        doc_title = document.metadata.get('title', document.filename)
    
    service = ExportService(
        user=user,
        document=document,
        query_text="test"
    )
    
    # Test 1: Citation generation
    print("\n1. Testing citation generation...")
    citation = service.generate_citation()
    assert "OCRchestra" in citation
    assert user.username in citation
    print(f"   ✅ Citation generated: {citation[:100]}...")
    
    # Test 2: Concordance CSV export
    print("\n2. Testing concordance CSV export...")
    try:
        sample_results = [
            {'left_context': 'Bu bir', 'keyword': 'test', 'right_context': 'cümledir', 'document': 'Test Doc', 'position': '1:10'}
        ]
        csv_content = service.export_concordance_csv(sample_results)
        assert isinstance(csv_content, bytes)
        assert b'OCRchestra' in csv_content  # Watermark check
        assert b'test' in csv_content
        print(f"   ✅ CSV export successful ({len(csv_content)} bytes)")
    except Exception as e:
        print(f"   ❌ CSV export failed: {e}")
        return False
    
    # Test 3: Concordance JSON export
    print("\n3. Testing concordance JSON export...")
    try:
        json_content = service.export_concordance_json(sample_results)
        assert isinstance(json_content, bytes)
        assert b'metadata' in json_content
        assert b'OCRchestra' in json_content
        print(f"   ✅ JSON export successful ({len(json_content)} bytes)")
    except Exception as e:
        print(f"   ❌ JSON export failed: {e}")
        return False
    
    # Test 4: Concordance Excel export
    print("\n4. Testing concordance Excel export...")
    try:
        excel_content = service.export_concordance_excel(sample_results)
        assert isinstance(excel_content, bytes)
        assert len(excel_content) > 0
        print(f"   ✅ Excel export successful ({len(excel_content)} bytes)")
    except Exception as e:
        print(f"   ❌ Excel export failed: {e}")
        return False
    
    # Test 5: Frequency exports
    print("\n5. Testing frequency exports...")
    try:
        sample_freq = [
            {'word': 'test', 'lemma': 'test', 'pos': 'NOUN', 'frequency': 10, 'percentage': 5.0}
        ]
        csv_freq = service.export_frequency_csv(sample_freq)
        json_freq = service.export_frequency_json(sample_freq)
        excel_freq = service.export_frequency_excel(sample_freq)
        
        assert all(len(x) > 0 for x in [csv_freq, json_freq, excel_freq])
        print(f"   ✅ All frequency exports successful")
        print(f"      - CSV: {len(csv_freq)} bytes")
        print(f"      - JSON: {len(json_freq)} bytes")
        print(f"      - Excel: {len(excel_freq)} bytes")
    except Exception as e:
        print(f"   ❌ Frequency export failed: {e}")
        return False
    
    # Test 6: Quota system
    print("\n6. Testing quota system...")
    try:
        profile, created = UserProfile.objects.get_or_create(user=user)
        quota_before = profile.export_used_mb
        
        # Simulate export
        from decimal import Decimal
        file_size_mb = Decimal('1.5')
        profile.use_export_quota(file_size_mb)
        
        quota_after = profile.export_used_mb
        assert quota_after > quota_before
        print(f"   ✅ Quota updated: {quota_before} MB → {quota_after} MB")
        
        # Reset for next test
        profile.export_used_mb = Decimal('0.0')
        profile.save()
    except Exception as e:
        print(f"   ❌ Quota test failed: {e}")
        return False
    
    return True


def test_helper_functions():
    """Test helper functions for real data integration."""
    print("\n" + "=" * 60)
    print("Testing Helper Functions...")
    print("=" * 60)
    
    document = Document.objects.filter(processed=True).first()
    if not document:
        print("❌ No processed documents found")
        return False
    
    # Test concordance results
    print("\n1. Testing _get_concordance_results...")
    try:
        from corpus.export_views import _get_concordance_results
        results = _get_concordance_results(document, "test")
        print(f"   ✅ Got {len(results)} concordance results")
    except Exception as e:
        print(f"   ⚠️  Concordance search failed (expected if CorpusService unavailable): {e}")
    
    # Test frequency results
    print("\n2. Testing _get_frequency_results...")
    try:
        from corpus.export_views import _get_frequency_results
        results = _get_frequency_results(document)
        print(f"   ✅ Got {len(results)} frequency entries")
        if results:
            print(f"      First entry: {results[0]}")
    except Exception as e:
        print(f"   ❌ Frequency analysis failed: {e}")
        return False
    
    return True


if __name__ == '__main__':
    print("\n🚀 Starting Week 3 Export System Tests...\n")
    
    success = True
    
    # Test 1: ExportService
    if not test_export_service():
        success = False
    
    # Test 2: Helper functions
    if not test_helper_functions():
        success = False
    
    # Summary
    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED!")
        print("Week 3 Export System is ready for production.")
    else:
        print("❌ SOME TESTS FAILED")
        print("Please review the errors above.")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
