from django.core.management.base import BaseCommand
from app.models import Client, ClientDomain

class Command(BaseCommand):
    help = 'Create the public tenant and its domain'

    def handle(self, *args, **options):
        # Check if the public tenant already exists
        if not Client.objects.filter(schema_name='public').exists():
            public_tenant = Client.objects.create(
                schema_name='public',
                name='Public Tenant',
                type='public'
            )
            self.stdout.write(self.style.SUCCESS('Public tenant created successfully.'))
        else:
            self.stdout.write(self.style.WARNING('Public tenant already exists. Skipping creation.'))

        # Create the primary domain for the public tenant
        if not ClientDomain.objects.filter(domain='domain.tld', tenant__schema_name='public').exists():
            public_domain = ClientDomain.objects.create(
                tenant=Client.objects.get(schema_name='public'),
                domain='localhost',
                is_primary=True
            )
            self.stdout.write(self.style.SUCCESS('Public domain created successfully.'))
        else:
            self.stdout.write(self.style.WARNING('Public domain already exists. Skipping creation.'))