from django.core.management.base import BaseCommand
from app.models import Client, ClientDomain

class Command(BaseCommand):
    public_tenant = Client.objects.get(schema_name='public')

    # Add the primary domain if it doesn't exist
    if not ClientDomain.objects.filter(tenant=public_tenant, domain='domain.tld').exists():
        ClientDomain.objects.create(
            tenant=public_tenant,
            domain='domain.tld',
            is_primary=True
        )