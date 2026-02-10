"""
Quick script to set admin password for testing
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ocrchestra_django.settings')
django.setup()

from django.contrib.auth.models import User

try:
    admin = User.objects.get(username='admin')
    admin.set_password('admin123')
    admin.is_superuser = True
    admin.is_staff = True
    admin.first_name = 'Admin'
    admin.last_name = 'User'
    admin.save()
    print(f"✓ Admin password set successfully!")
    print(f"  Username: admin")
    print(f"  Password: admin123")
except User.DoesNotExist:
    admin = User.objects.create_superuser('admin', 'admin@corpuslio.com', 'admin123')
    admin.first_name = 'Admin'
    admin.last_name = 'User'
    admin.save()
    print(f"✓ Admin user created successfully!")
    print(f"  Username: admin")
    print(f"  Password: admin123")
