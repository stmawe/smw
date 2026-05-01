"""
Shop creation with automatic SSL certificate generation
Call this to create a shop and automatically add SSL on Serv00
Usage: python manage.py create_shop_with_ssl --name "Shop Name" --owner username
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from mydak.models import Shop
import subprocess
import os

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a shop and automatically generate SSL certificate'
    
    def add_arguments(self, parser):
        parser.add_argument('--name', type=str, required=True, help='Shop name')
        parser.add_argument('--owner', type=str, required=True, help='Owner username')
        parser.add_argument('--category', type=str, default='other', help='Shop category')
        parser.add_argument('--description', type=str, default='', help='Shop description')
        parser.add_argument('--no-ssl', action='store_true', help='Skip SSL generation')
    
    def handle(self, *args, **options):
        shop_name = options['name']
        owner_username = options['owner']
        
        self.stdout.write(self.style.WARNING(f'Creating shop: {shop_name}'))
        
        # Get owner
        try:
            owner = User.objects.get(username=owner_username)
        except User.DoesNotExist:
            raise CommandError(f'User "{owner_username}" not found')
        
        # Check shop limit
        shop_count = Shop.objects.filter(owner=owner).count()
        if shop_count >= 2:
            raise CommandError(f'User {owner_username} has reached max 2 shops')
        
        # Create shop
        from app.shop_urls import generate_shop_slug
        slug = generate_shop_slug(shop_name)
        
        shop = Shop.objects.create(
            name=shop_name,
            slug=slug,
            owner=owner,
            category=options['category'],
            description=options['description']
        )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Shop created: {shop.name} ({shop.slug})'))
        
        # Generate SSL if not disabled
        if not options['no_ssl']:
            shop_domain = f'{slug}.smw.pgwiz.cloud'
            self.generate_ssl(shop_domain)
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Shop ready at: https://{slug}.smw.pgwiz.cloud/'))
    
    def generate_ssl(self, domain):
        """Generate SSL certificate for shop domain"""
        self.stdout.write(self.style.WARNING(f'Generating SSL for: {domain}'))
        
        ip_address = '128.204.223.70'
        
        try:
            # Use devil ssl command (Serv00 native)
            cmd = f'devil ssl www add {ip_address} le le {domain}'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0 or 'Certificate added' in result.stdout:
                self.stdout.write(self.style.SUCCESS(f'✓ SSL certificate generated for {domain}'))
            else:
                self.stdout.write(self.style.WARNING(f'~ SSL generation may have issues: {result.stderr}'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ SSL generation failed: {str(e)}'))
