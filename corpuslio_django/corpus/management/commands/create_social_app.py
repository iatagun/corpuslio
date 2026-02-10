from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Create or update Google SocialApp for django-allauth using env vars: GOOGLE_CLIENT_ID and GOOGLE_SECRET'

    def handle(self, *args, **options):
        try:
            from allauth.socialaccount.models import SocialApp
            from django.contrib.sites.models import Site
        except Exception as e:
            self.stderr.write('Error importing allauth or Site models: %s' % e)
            return

        client_id = settings.GOOGLE_CLIENT_ID if hasattr(settings, 'GOOGLE_CLIENT_ID') else None
        secret = settings.GOOGLE_CLIENT_SECRET if hasattr(settings, 'GOOGLE_CLIENT_SECRET') else None
        site_id = getattr(settings, 'SITE_ID', 1)

        if not client_id or not secret:
            self.stderr.write('GOOGLE_CLIENT_ID and/or GOOGLE_CLIENT_SECRET not set in settings or env. Aborting.')
            return

        site = Site.objects.filter(pk=site_id).first()
        if not site:
            self.stderr.write(f'Site with id={site_id} not found. Create one in admin first.')
            return

        app, created = SocialApp.objects.get_or_create(provider='google', name='Google')
        app.client_id = client_id
        app.secret = secret
        app.save()
        app.sites.clear()
        app.sites.add(site)

        if created:
            self.stdout.write('Created SocialApp for Google and attached to site %s' % site.domain)
        else:
            self.stdout.write('Updated SocialApp for Google and attached to site %s' % site.domain)
