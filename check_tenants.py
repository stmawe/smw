#!/usr/bin/env python3
import os
import sys
import django

# Set up Django
sys.path.insert(0, '/usr/home/wiptech/domains/smw.pgwiz.cloud/public_python')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')
django.setup()

from app.models import Client, ClientDomain

print("=== TENANTS ===")
for client in Client.objects.all():
    print(f"ID: {client.id}, Name: {client.name}, Type: {client.tenant_type}, Schema: {client.schema_name}")

print("\n=== DOMAINS ===")
for domain in ClientDomain.objects.all():
    print(f"Domain: {domain.domain}, Tenant: {domain.tenant_id}")
