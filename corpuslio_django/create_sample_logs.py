"""
Create sample logs for the current logged-in user.
Run this after logging in to see logs in profile page.
"""

import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'corpuslio_django.settings')
django.setup()

from django.contrib.auth.models import User
from corpus.models import QueryLog, ExportLog, UserProfile
from decimal import Decimal

def create_sample_logs(username):
    """Create sample logs for demonstration."""
    try:
        user = User.objects.get(username=username)
        print(f"✓ Found user: {username}")
    except User.DoesNotExist:
        print(f"✗ User '{username}' not found!")
        print("\nAvailable users:")
        for u in User.objects.all():
            print(f"  - {u.username} (ID: {u.id}, Superuser: {u.is_superuser})")
        return
    
    # Get or create profile
    profile, created = UserProfile.objects.get_or_create(user=user)
    print(f"✓ Profile: {profile.get_role_display()}")
    
    # Create 5 sample query logs
    print("\n📊 Creating Query Logs...")
    sample_queries = [
        {'text': 'ayna nöronları', 'type': 'word', 'results': 23},
        {'text': 'mirror neurons', 'type': 'lemma', 'results': 45},
        {'text': 'language acquisition', 'type': 'advanced', 'results': 67},
        {'text': 'cognitive', 'type': 'concordance', 'results': 89},
        {'text': 'neuroscience', 'type': 'frequency', 'results': 120},
    ]
    
    for i, query in enumerate(sample_queries, 1):
        log = QueryLog.objects.create(
            user=user,
            ip_address='127.0.0.1',
            user_agent='Mozilla/5.0 (Test Browser)',
            query_text=query['text'],
            query_type=query['type'],
            result_count=query['results'],
            execution_time_ms=50 + (i * 10),
            is_cached=(i % 2 == 0),
            rate_limit_hit=False,
            daily_query_count=profile.queries_today
        )
        print(f"  {i}. Created: '{query['text']}' ({query['type']}) - {query['results']} results")
    
    # Create 3 sample export logs
    print("\n📦 Creating Export Logs...")
    sample_exports = [
        {'type': 'concordance', 'format': 'csv', 'size_mb': 1.2},
        {'type': 'frequency', 'format': 'json', 'size_mb': 0.8},
        {'type': 'document', 'format': 'pdf', 'size_mb': 2.5},
    ]
    
    quota_before = profile.export_used_mb
    
    for i, export in enumerate(sample_exports, 1):
        size_bytes = int(export['size_mb'] * 1024 * 1024)
        quota_after = quota_before + Decimal(str(export['size_mb']))
        
        log = ExportLog.objects.create(
            user=user,
            ip_address='127.0.0.1',
            export_type=export['type'],
            format=export['format'],
            query_text=f"Sample export {i}",
            row_count=100 * i,
            file_size_bytes=size_bytes,
            watermark_applied=True,
            citation_text=f"OCRchestra Export {i}",
            quota_before_mb=quota_before,
            quota_after_mb=quota_after
        )
        print(f"  {i}. Created: {export['type']}/{export['format']} - {export['size_mb']} MB")
        quota_before = quota_after
    
    # Update profile quotas
    profile.queries_today = 5
    profile.export_used_mb = quota_before
    profile.save()
    
    print(f"\n✅ Sample logs created successfully!")
    print(f"\n📊 Profile Stats:")
    print(f"  Queries Today: {profile.queries_today}")
    print(f"  Export Used: {profile.export_used_mb} MB")
    print(f"\n🔗 View profile: http://127.0.0.1:8000/corpus/profile/")
    print(f"🔗 Admin Query Logs: http://127.0.0.1:8000/admin/corpus/querylog/")
    print(f"🔗 Admin Export Logs: http://127.0.0.1:8000/admin/corpus/exportlog/")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎯 Create Sample Logs for User")
    print("="*60)
    
    # Check if username provided
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        # Try to find the first active user
        users = User.objects.filter(is_active=True).exclude(username='test_researcher').exclude(username='test_superuser')
        if users.exists():
            username = users.first().username
            print(f"\n💡 No username provided, using first active user: {username}")
        else:
            print("\n❌ No active users found!")
            print("\nUsage: python create_sample_logs.py <username>")
            print("\nAvailable users:")
            for u in User.objects.all():
                print(f"  - {u.username}")
            sys.exit(1)
    
    create_sample_logs(username)
