"""
Management command to create UserProfile instances for all existing users.
This is needed after adding the UserProfile model to ensure backwards compatibility.

Usage:
    python manage.py create_user_profiles
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from corpus.models import UserProfile


class Command(BaseCommand):
    help = 'Create UserProfile instances for all existing users who do not have one'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating profiles',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Get all users
        all_users = User.objects.all()
        total_users = all_users.count()
        
        self.stdout.write(f"Found {total_users} total users")
        
        # Find users without profiles
        users_without_profiles = []
        for user in all_users:
            try:
                # Try to access the profile
                _ = user.profile
            except UserProfile.DoesNotExist:
                users_without_profiles.append(user)
        
        if not users_without_profiles:
            self.stdout.write(self.style.SUCCESS('✅ All users already have profiles!'))
            return
        
        self.stdout.write(f"Found {len(users_without_profiles)} users without profiles")
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n🔍 DRY RUN - No changes will be made\n'))
            for user in users_without_profiles:
                self.stdout.write(f"  Would create profile for: {user.username} ({user.email})")
            return
        
        # Create profiles
        created_count = 0
        for user in users_without_profiles:
            profile = UserProfile.objects.create(
                user=user,
                role='registered',  # Default role for existing users
            )
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f"✅ Created profile for: {user.username} (role: {profile.role})")
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 Successfully created {created_count} UserProfile instances!')
        )
        
        # Show summary
        self.stdout.write('\n📊 Summary:')
        self.stdout.write(f"  Total users: {total_users}")
        self.stdout.write(f"  Profiles created: {created_count}")
        self.stdout.write(f"  Users with profiles: {total_users}")
