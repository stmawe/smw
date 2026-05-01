"""
Management command to set up admin subdomain as a public tenant
Usage: python manage.py setup_admin_tenant
"""

from django.core.management.base import BaseCommand
from django.db import connection
from app.models import Client, ClientDomain


class Command(BaseCommand):
    help = 'Set up admin.smw.pgwiz.cloud as a public tenant for admin dashboard'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Setting up admin tenant...'))
        
        # Check if admin tenant already exists
        admin_tenant = Client.objects.filter(schema_name='admin').first()
        
        if admin_tenant:
            self.stdout.write(self.style.SUCCESS('✓ Admin tenant already exists'))
        else:
            # Create admin tenant
            admin_tenant = Client.objects.create(
                schema_name='admin',
                name='Admin Dashboard',
                description='Public admin subdomain for dashboard access'
            )
            self.stdout.write(self.style.SUCCESS('✓ Admin tenant created'))
        
        # Check if domain is registered
        admin_domain = ClientDomain.objects.filter(domain='admin.smw.pgwiz.cloud').first()
        
        if admin_domain:
            self.stdout.write(self.style.SUCCESS('✓ Admin domain already registered'))
        else:
            # Register admin subdomain
            admin_domain = ClientDomain.objects.create(
                tenant=admin_tenant,
                domain='admin.smw.pgwiz.cloud',
                is_primary=True
            )
            self.stdout.write(self.style.SUCCESS('✓ Admin domain registered'))
        
        self.stdout.write(self.style.SUCCESS('\n✓ Admin tenant setup complete!'))
        self.stdout.write('Access at: https://admin.smw.pgwiz.cloud/\n')
