"""
Management command: backfill_ssl

Issues Let's Encrypt SSL certificates for all active users who have
a Cloudflare DNS record but no SSL cert yet.

Usage:
    python manage.py backfill_ssl
    python manage.py backfill_ssl --username bwarex
"""

import subprocess
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Issue devil SSL certs for existing user subdomains'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default=None)

    def handle(self, *args, **options):
        from app.models import User

        base_domain = getattr(settings, 'BASE_DOMAIN', 'smw.pgwiz.cloud')
        server_ip = getattr(settings, 'SERVER_IP', '128.204.223.70')
        target = options.get('username')

        if target:
            users = User.objects.filter(username=target)
        else:
            users = User.objects.filter(is_active=True).order_by('username')

        total = users.count()
        self.stdout.write(f'Processing {total} user(s)...')
        done = failed = 0

        for user in users:
            subdomain = f'{user.username}.{base_domain}'
            try:
                result = subprocess.run(
                    ['devil', 'ssl', 'www', 'add', server_ip, 'le', 'le', subdomain],
                    capture_output=True, text=True, timeout=120,
                )
                if result.returncode == 0:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ {subdomain}'))
                    done += 1
                else:
                    msg = result.stderr or result.stdout
                    self.stderr.write(self.style.WARNING(f'  ✗ {subdomain}: {msg.strip()}'))
                    failed += 1
            except Exception as exc:
                self.stderr.write(self.style.WARNING(f'  ✗ {subdomain}: {exc}'))
                failed += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Done. Issued: {done}, Failed: {failed}'))
