"""
Management command: backfill_dns

Creates Cloudflare DNS A records for all existing users who don't have one yet.
Safe to run multiple times — skips records that already exist.

Usage:
    python manage.py backfill_dns
    python manage.py backfill_dns --username b.ware
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Backfill Cloudflare DNS A records for existing users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default=None,
            help='Only create DNS for this specific username',
        )

    def handle(self, *args, **options):
        from app.models import User
        from app.cloudflare_dns import create_subdomain_dns_record

        target = options.get('username')

        if target:
            users = User.objects.filter(username=target)
            if not users.exists():
                self.stderr.write(self.style.ERROR(f'User "{target}" not found'))
                return
        else:
            users = User.objects.filter(is_active=True).order_by('username')

        total = users.count()
        self.stdout.write(f'Processing {total} user(s)...')

        done = failed = 0
        for user in users:
            try:
                create_subdomain_dns_record(user.username)
                self.stdout.write(self.style.SUCCESS(f'  ✓ {user.username}'))
                done += 1
            except Exception as exc:
                self.stderr.write(self.style.WARNING(f'  ✗ {user.username}: {exc}'))
                failed += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Done. Processed: {done}, Failed: {failed}'))
