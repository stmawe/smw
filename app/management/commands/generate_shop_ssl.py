"""
Management command to generate SSL certificate for a shop
Usage: python manage.py generate_shop_ssl shop_name [--shop-id ID]
"""

from django.core.management.base import BaseCommand, CommandError
from app.ssl_tasks import generate_ssl_sync


class Command(BaseCommand):
    help = 'Generate SSL certificate for a shop domain'
    
    def add_arguments(self, parser):
        parser.add_argument('shop_name', type=str, help='Shop name for SSL generation')
        parser.add_argument(
            '--shop-id',
            type=int,
            default=None,
            help='Shop ID to update with SSL info'
        )
        parser.add_argument(
            '--async',
            action='store_true',
            help='Generate asynchronously (non-blocking)'
        )
    
    def handle(self, *args, **options):
        shop_name = options['shop_name']
        shop_id = options.get('shop_id')
        async_mode = options.get('async', False)
        
        self.stdout.write(
            self.style.WARNING(f'Generating SSL certificate for: {shop_name}')
        )
        
        if async_mode:
            from app.ssl_tasks import generate_ssl_async
            thread = generate_ssl_async(shop_name, shop_id)
            self.stdout.write(
                self.style.SUCCESS(
                    f'SSL generation started in background (thread: {thread.name})'
                )
            )
        else:
            result = generate_ssl_sync(shop_name, shop_id)
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(f"✓ {result.get('message', 'Certificate generated')}")
                )
                if 'subdomain' in result:
                    self.stdout.write(f"  Subdomain: {result['subdomain']}")
                if 'cert_path' in result:
                    self.stdout.write(f"  Path: {result['cert_path']}")
            else:
                raise CommandError(f"SSL generation failed: {result.get('error', 'Unknown error')}")
