import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ocrchestra_django.settings')
django.setup()

from django.contrib.auth.models import User

print("\n🔍 Tüm Kullanıcılar:")
for u in User.objects.all():
    print(f"  - {u.username} (ID: {u.id}, Superuser: {u.is_superuser})")
