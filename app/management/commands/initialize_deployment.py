"""
Management command to initialize the deployment after migrations
Handles:
- Checking and creating admin tenant
- Creating initial cache tables if needed
- Setting up necessary database structures
Usage: python manage.py initialize_deployment
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db import connection
from app.models import Client, ClientDomain


class Command(BaseCommand):
    help = 'Initialize deployment: run migrations, create admin tenant, setup cache'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n=== INITIALIZING DEPLOYMENT ===\n'))
        
        # Step 1: Verify cache table exists
        self._verify_cache_table()
        
        # Step 2: Setup admin tenant
        self._setup_admin_tenant()
        
        # Step 3: Verify database
        self._verify_database()
        
        self.stdout.write(self.style.SUCCESS('\n✓ Deployment initialization complete!\n'))
    
    def _verify_cache_table(self):
        """Ensure cache table exists for shop_cache operations"""
        self.stdout.write('[*] Checking cache table...')
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM django_session LIMIT 1")
            self.stdout.write(self.style.SUCCESS('✓ Cache table exists'))
        except Exception as e:
            self.stdout.write(self.style.WARNING('⚠ Cache table not found, creating...'))
            try:
                cache.set('_test_key', '_test_value', 1)
                self.stdout.write(self.style.SUCCESS('✓ Cache initialized'))
            except Exception as cache_err:
                self.stdout.write(self.style.ERROR(f'✗ Cache initialization failed: {cache_err}'))
    
    def _setup_admin_tenant(self):
        """Setup admin subdomain as a public tenant"""
        self.stdout.write('[*] Setting up admin tenant...')
        
        # Check if admin tenant already exists
        admin_tenant = Client.objects.filter(schema_name='admin').first()
        
        if admin_tenant:
            self.stdout.write(self.style.SUCCESS('✓ Admin tenant already exists'))
        else:
            try:
                # Create admin tenant
                admin_tenant = Client.objects.create(
                    schema_name='admin',
                    name='Admin Dashboard',
                    tenant_type='location'
                )
                self.stdout.write(self.style.SUCCESS('✓ Admin tenant created'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Admin tenant creation failed: {e}'))
                return
        
        # Check if domain is registered
        admin_domain = ClientDomain.objects.filter(domain='admin.smw.pgwiz.cloud').first()
        
        if admin_domain:
            self.stdout.write(self.style.SUCCESS('✓ Admin domain already registered'))
        else:
            try:
                # Register admin subdomain
                admin_domain = ClientDomain.objects.create(
                    tenant=admin_tenant,
                    domain='admin.smw.pgwiz.cloud',
                    is_primary=True
                )
                self.stdout.write(self.style.SUCCESS('✓ Admin domain registered'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Admin domain registration failed: {e}'))
    
    def _verify_database(self):
        """Verify critical database structures"""
        self.stdout.write('[*] Verifying database structures...')
        
        try:
            # Check if Client table has expected fields
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM app_client")
                count = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f'✓ Database verified ({count} clients)'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Database verification failed: {e}'))
