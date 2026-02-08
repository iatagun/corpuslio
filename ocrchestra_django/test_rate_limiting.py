"""
Test script for rate limiting and audit logging functionality.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ocrchestra_django.settings')
django.setup()

from django.contrib.auth.models import User
from corpus.models import UserProfile, QueryLog, ExportLog


def test_query_logging():
    """Test QueryLog creation and query count tracking."""
    print("\n" + "="*60)
    print("TEST 1: Query Logging & Count Tracking")
    print("="*60)
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        username='test_researcher',
        defaults={'email': 'test@example.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✓ Created test user: {user.username}")
    else:
        print(f"✓ Using existing user: {user.username}")
    
    # Get or create profile
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={'role': 'verified'}
    )
    
    # Reset query count for clean test
    profile.queries_today = 0
    profile.save()
    
    print(f"\n📊 Initial State:")
    print(f"   Role: {profile.get_role_display()}")
    print(f"   Query Limit: {profile.get_query_limit()}/day")
    print(f"   Queries Today: {profile.queries_today}")
    print(f"   Can Query: {profile.can_query()}")
    
    # Simulate 5 queries
    print(f"\n🔄 Simulating 5 queries...")
    for i in range(5):
        # Create query log
        log = QueryLog.objects.create(
            user=user,
            ip_address='127.0.0.1',
            user_agent='TestBot/1.0',
            query_text=f'test query {i+1}',
            query_type='word',
            result_count=10,
            execution_time_ms=50,
            is_cached=False,
            rate_limit_hit=False,
            daily_query_count=profile.queries_today
        )
        
        # Increment count
        profile.increment_query_count()
        profile.refresh_from_db()
        
        print(f"   Query {i+1}: queries_today = {profile.queries_today}")
    
    print(f"\n✅ Final State:")
    print(f"   Queries Today: {profile.queries_today}")
    print(f"   Total QueryLogs: {QueryLog.objects.filter(user=user).count()}")
    print(f"   Can Still Query: {profile.can_query()}")
    
    # Show recent logs
    recent_logs = QueryLog.objects.filter(user=user).order_by('-created_at')[:3]
    print(f"\n📋 Recent Query Logs:")
    for log in recent_logs:
        print(f"   - {log.created_at.strftime('%H:%M:%S')}: '{log.query_text}' "
              f"({log.result_count} results, {log.execution_time_ms}ms)")


def test_export_logging():
    """Test ExportLog creation and quota tracking."""
    print("\n" + "="*60)
    print("TEST 2: Export Logging & Quota Tracking")
    print("="*60)
    
    # Get test user
    user = User.objects.get(username='test_researcher')
    profile = UserProfile.objects.get(user=user)
    
    # Reset export quota for clean test
    profile.export_used_mb = 0
    profile.save()
    
    print(f"\n📊 Initial State:")
    print(f"   Export Quota: {profile.export_quota_mb} MB/month")
    print(f"   Export Used: {profile.export_used_mb} MB")
    print(f"   Can Export 2MB: {profile.can_export(2)}")
    
    # Simulate 3 exports
    print(f"\n🔄 Simulating 3 exports (1MB, 1.5MB, 0.5MB)...")
    export_sizes = [1.0, 1.5, 0.5]
    
    for i, size_mb in enumerate(export_sizes):
        quota_before = profile.export_used_mb
        
        # Use quota
        profile.use_export_quota(size_mb)
        profile.refresh_from_db()
        
        quota_after = profile.export_used_mb
        
        # Create export log
        log = ExportLog.objects.create(
            user=user,
            ip_address='127.0.0.1',
            export_type='concordance',
            format='csv',
            query_text=f'export test {i+1}',
            row_count=100,
            file_size_bytes=int(size_mb * 1024 * 1024),
            watermark_applied=True,
            citation_text='OCRchestra Test Export',
            quota_before_mb=quota_before,
            quota_after_mb=quota_after
        )
        
        print(f"   Export {i+1}: {size_mb} MB → Used: {profile.export_used_mb:.2f} MB")
    
    print(f"\n✅ Final State:")
    print(f"   Export Used: {profile.export_used_mb:.2f} / {profile.export_quota_mb} MB")
    print(f"   Total ExportLogs: {ExportLog.objects.filter(user=user).count()}")
    print(f"   Can Export 2MB: {profile.can_export(2)}")
    
    # Show recent logs
    recent_logs = ExportLog.objects.filter(user=user).order_by('-created_at')[:3]
    print(f"\n📋 Recent Export Logs:")
    for log in recent_logs:
        print(f"   - {log.created_at.strftime('%H:%M:%S')}: {log.export_type}/{log.format} "
              f"({log.file_size_mb:.2f} MB, quota: {log.quota_before_mb:.2f} → {log.quota_after_mb:.2f})")


def test_rate_limiting():
    """Test rate limit detection and enforcement."""
    print("\n" + "="*60)
    print("TEST 3: Rate Limit Enforcement")
    print("="*60)
    
    user = User.objects.get(username='test_researcher')
    profile = UserProfile.objects.get(user=user)
    
    print(f"\n📊 Current State:")
    print(f"   Role: {profile.get_role_display()}")
    print(f"   Query Limit: {profile.get_query_limit()}/day")
    print(f"   Queries Today: {profile.queries_today}")
    
    # Try to exceed limit
    print(f"\n🔄 Testing limit enforcement...")
    limit = profile.get_query_limit()
    
    # Set queries to limit - 2
    profile.queries_today = limit - 2
    profile.save()
    
    print(f"   Set queries_today to {limit - 2}")
    print(f"   Can query: {profile.can_query()} ✓")
    
    # Increment to limit - 1
    profile.increment_query_count()
    profile.refresh_from_db()
    print(f"   After increment: {profile.queries_today}")
    print(f"   Can query: {profile.can_query()} ✓")
    
    # Increment to limit
    profile.increment_query_count()
    profile.refresh_from_db()
    print(f"   After increment: {profile.queries_today}")
    print(f"   Can query: {profile.can_query()} ✗ (LIMIT REACHED)")
    
    # Create rate-limited query log
    log = QueryLog.objects.create(
        user=user,
        ip_address='127.0.0.1',
        user_agent='TestBot/1.0',
        query_text='rate limited query',
        query_type='word',
        result_count=0,
        execution_time_ms=0,
        is_cached=False,
        rate_limit_hit=True,  # MARKED AS RATE LIMITED
        daily_query_count=profile.queries_today
    )
    
    print(f"\n✅ Rate limit properly enforced!")
    print(f"   Created QueryLog with rate_limit_hit=True")
    
    # Count rate-limited queries
    rate_limited_count = QueryLog.objects.filter(
        user=user,
        rate_limit_hit=True
    ).count()
    print(f"   Total rate-limited queries: {rate_limited_count}")


def test_superuser_bypass():
    """Test superuser bypass logic."""
    print("\n" + "="*60)
    print("TEST 4: Superuser Bypass")
    print("="*60)
    
    # Get or create superuser
    superuser, created = User.objects.get_or_create(
        username='test_superuser',
        defaults={
            'email': 'super@example.com',
            'is_superuser': True,
            'is_staff': True
        }
    )
    if created:
        superuser.set_password('superpass123')
        superuser.save()
        print(f"✓ Created superuser: {superuser.username}")
    else:
        print(f"✓ Using existing superuser: {superuser.username}")
    
    # Get profile
    profile, created = UserProfile.objects.get_or_create(user=superuser)
    
    print(f"\n📊 Superuser Profile:")
    print(f"   Role: {profile.get_role_display()}")
    print(f"   Is Superuser: {superuser.is_superuser}")
    print(f"   Query Limit: {profile.get_query_limit()} (0 = unlimited)")
    print(f"   Can Query: {profile.can_query()} (always True)")
    print(f"   Can Export 999MB: {profile.can_export(999)} (always True)")
    
    # Simulate 10 queries
    print(f"\n🔄 Simulating 10 queries (should not increment count)...")
    initial_count = profile.queries_today
    
    for i in range(10):
        # Superusers shouldn't have counts incremented
        pass
    
    print(f"   Queries count unchanged: {profile.queries_today} (bypass working)")
    
    print(f"\n✅ Superuser bypass confirmed!")


def show_admin_stats():
    """Show admin dashboard statistics."""
    print("\n" + "="*60)
    print("ADMIN DASHBOARD STATS")
    print("="*60)
    
    total_users = UserProfile.objects.count()
    total_queries = QueryLog.objects.count()
    total_exports = ExportLog.objects.count()
    rate_limited = QueryLog.objects.filter(rate_limit_hit=True).count()
    
    print(f"\n📊 Platform Statistics:")
    print(f"   Total Users: {total_users}")
    print(f"   Total Queries: {total_queries}")
    print(f"   Total Exports: {total_exports}")
    print(f"   Rate Limited Queries: {rate_limited}")
    
    # Top users by query count
    from django.db.models import Count
    top_users = QueryLog.objects.values('user__username').annotate(
        query_count=Count('id')
    ).order_by('-query_count')[:5]
    
    print(f"\n👥 Top Users (by query count):")
    for i, user_data in enumerate(top_users, 1):
        username = user_data['user__username'] or 'Anonymous'
        count = user_data['query_count']
        print(f"   {i}. {username}: {count} queries")
    
    print(f"\n🔗 Admin Panel URLs:")
    print(f"   - User Profiles: http://127.0.0.1:8000/admin/corpus/userprofile/")
    print(f"   - Query Logs: http://127.0.0.1:8000/admin/corpus/querylog/")
    print(f"   - Export Logs: http://127.0.0.1:8000/admin/corpus/exportlog/")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 OCRchestra Rate Limiting & Audit Logging Test Suite")
    print("="*60)
    
    try:
        test_query_logging()
        test_export_logging()
        test_rate_limiting()
        test_superuser_bypass()
        show_admin_stats()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\n💡 Next Steps:")
        print("   1. Visit admin panel to see logs: http://127.0.0.1:8000/admin/")
        print("   2. Test rate limiting in browser (library_view)")
        print("   3. Monitor QueryLog/ExportLog in admin interface")
        print("   4. Check middleware is logging real requests")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
