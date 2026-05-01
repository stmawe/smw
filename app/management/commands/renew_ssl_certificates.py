"""
Management command to renew SSL certificates nearing expiration
Usage: python manage.py renew_ssl_certificates [--days 30]
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from mydak.models import Shop
from app.ssl_tasks import generate_ssl_async
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check and renew expiring SSL certificates'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Renew certificates expiring within N days (default: 30)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force renewal of all active SSL certificates'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        force = options.get('force', False)
        
        now = timezone.now()
        renewal_window = now + timedelta(days=days)
        
        if force:
            shops = Shop.objects.filter(has_ssl=True)
            self.stdout.write(
                self.style.WARNING(f'Force renewing {shops.count()} SSL certificates...')
            )
        else:
            shops = Shop.objects.filter(
                has_ssl=True,
                ssl_expires_at__lte=renewal_window,
                ssl_expires_at__gt=now
            )
            self.stdout.write(
                self.style.WARNING(
                    f'Found {shops.count()} certificates expiring within {days} days'
                )
            )
        
        renewed = 0
        errors = []
        
        for shop in shops:
            try:
                self.stdout.write(
                    f'Renewing SSL for: {shop.slug} (expires: {shop.ssl_expires_at})'
                )
                thread = generate_ssl_async(shop.name, shop.id)
                renewed += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Renewal queued'))
                
            except Exception as e:
                error_msg = f"Error renewing {shop.slug}: {str(e)}"
                self.stdout.write(self.style.ERROR(f'✗ {error_msg}'))
                errors.append(error_msg)
                logger.exception(f'SSL renewal failed for shop {shop.id}')
        
        summary = f"Queued {renewed} certificate renewals"
        if errors:
            summary += f" ({len(errors)} errors)"
            self.stdout.write(self.style.ERROR(summary))
        else:
            self.stdout.write(self.style.SUCCESS(summary))
