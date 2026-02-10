"""
Clear sample logs for a specific user.
"""

import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ocrchestra_django.settings')
django.setup()

from django.contrib.auth.models import User
from corpus.models import QueryLog, ExportLog, UserProfile

def clear_logs(username):
    """Clear all logs for a user."""
    try:
        user = User.objects.get(username=username)
        print(f"✓ Found user: {username}")
    except User.DoesNotExist:
        print(f"✗ User '{username}' not found!")
        return
    
    # Count logs
    query_count = QueryLog.objects.filter(user=user).count()
    export_count = ExportLog.objects.filter(user=user).count()
    
    print(f"\n📊 Found {query_count} query logs and {export_count} export logs")
    
    if query_count == 0 and export_count == 0:
        print("Nothing to delete.")
        return
    
    # Delete all logs
    QueryLog.objects.filter(user=user).delete()
    ExportLog.objects.filter(user=user).delete()
    
    # Reset profile counters
    profile = UserProfile.objects.get(user=user)
    profile.queries_today = 0
    profile.export_used_mb = 0
    profile.save()
    
    print(f"\n✅ Cleared all logs for {username}")
    print(f"📊 Profile reset: queries_today=0, export_used_mb=0")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        username = input("Enter username to clear logs: ")
    
    clear_logs(username)
