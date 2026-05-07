"""
Management command: fix_client_domains

Fixes ClientDomain records that were created with .localhost suffix
(when BASE_DOMAIN was incorrectly set to localhost).
Replaces them with the correct .smw.pgwiz.cloud suffix.

Usage:
    python manage.py fix_client_domains
"""

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Fix ClientDomain records with .localhost suffix'

    def handle(self, *args, **options):
        from app.models import ClientDomain

        base_domain = getattr(settings, 'BASE_DOMAIN', 'smw.pgwiz.cloud')

        # Find all .localhost domains
        bad_domains = ClientDomain.objects.filter(domain__endswith='.localhost')
        count = bad_domains.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('No .localhost domains found — nothing to fix.'))
        else:
            self.stdout.write(f'Found {count} domain(s) to fix:')
            for cd in bad_domains:
                old = cd.domain
                # Replace .localhost with .smw.pgwiz.cloud
                new = old.replace('.localhost', f'.{base_domain}')
                cd.domain = new
                cd.save(update_fields=['domain'])
                self.stdout.write(self.style.SUCCESS(f'  {old} → {new}'))

        self.stdout.write('\nAll ClientDomain records:')
        for cd in ClientDomain.objects.all().order_by('domain'):
            self.stdout.write(f'  {cd.domain}  (schema: {cd.tenant.schema_name})')
