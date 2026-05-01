#!/usr/bin/env python3
"""Diagnostic script to check tenant and domain setup"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')
os.environ['DB_HOST'] = os.getenv('DB_HOST', 'pgsql3.serv00.com')
os.environ['DB_NAME'] = os.getenv('DB_NAME', 'p7152_smw')
os.environ['DB_USER'] = os.getenv('DB_USER', 'p7152_smw')
os.environ['DB_PASS'] = os.getenv('DB_PASS', '')

# Configure Django settings before importing models
from django.conf import settings
if not settings.configured:
    from config.settings.prod import *

django.setup()

from app.models import Client, ClientDomain

print("=== REGISTERED TENANTS ===")
for client in Client.objects.all():
    print(f"  ID: {client.id}")
    print(f"  Name: {client.name}")
    print(f"  Schema: {client.schema_name}")
    print(f"  Type: {client.tenant_type}")
    print()

print("=== REGISTERED DOMAINS ===")
for domain in ClientDomain.objects.all():
    client = domain.tenant
    print(f"  Domain: {domain.domain}")
    print(f"  Tenant: {client.name} (ID: {client.id}, Schema: {client.schema_name})")
    print(f"  Primary: {domain.is_primary}")
    print()
