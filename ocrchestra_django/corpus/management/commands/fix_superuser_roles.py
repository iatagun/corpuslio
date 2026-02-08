"""
Management command to update superuser profiles to admin role.

Usage:
    python manage.py fix_superuser_roles
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from corpus.models import UserProfile


class Command(BaseCommand):
    help = 'Update superuser profiles to admin role'

    def handle(self, *args, **options):
        # Get all superusers
        superusers = User.objects.filter(is_superuser=True)
        
        if not superusers.exists():
            self.stdout.write(self.style.WARNING('No superusers found.'))
            return
        
        self.stdout.write(f"Found {superusers.count()} superuser(s)")
        
        updated_count = 0
        for user in superusers:
            try:
                profile = user.profile
                if profile.role != 'admin':
                    old_role = profile.role
                    profile.role = 'admin'
                    profile.export_quota_mb = 999999  # Unlimited export (practically)
                    profile.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ Updated {user.username}: {old_role} → admin"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ {user.username} already admin"
                        )
                    )
            except UserProfile.DoesNotExist:
                # Create profile for superuser
                profile = UserProfile.objects.create(
                    user=user,
                    role='admin',
                    export_quota_mb=999999
                )
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Created admin profile for {user.username}"
                    )
                )
        
        if updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🎉 Updated {updated_count} superuser profile(s) to admin role!'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\n✅ All superusers already have admin role!')
            )
