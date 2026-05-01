"""
Test script to debug domain extraction
"""

# Test what django-tenants would extract from the hostname
test_host = "admin.smw.pgwiz.cloud"

# Split by dots
parts = test_host.split('.')
print(f"Host: {test_host}")
print(f"Parts: {parts}")
print(f"Subdomain: {parts[0]}")
print(f"Base domain: {'.'.join(parts[1:])}")

# Check configuration values
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.prod'
os.environ['DB_HOST'] = 'pgsql3.serv00.com'
os.environ['DB_NAME'] = 'p7152_smw'
os.environ['DB_USER'] = 'p7152_smw'

# Django settings that matter
PUBLIC_SCHEMA_NAME = 'public'
BASE_DOMAIN = 'smw.pgwiz.cloud'

print(f"\nBase domain from settings: {BASE_DOMAIN}")
print(f"Public schema: {PUBLIC_SCHEMA_NAME}")

# How django-tenants extracts subdomain
if test_host.endswith(BASE_DOMAIN):
    subdomain = test_host.replace(f'.{BASE_DOMAIN}', '')
    print(f"\nExtracted subdomain: '{subdomain}'")
    if subdomain == '':
        print("This is the public domain")
    else:
        print(f"Looking for tenant with schema or subdomain: '{subdomain}'")
else:
    print(f"\nHost doesn't end with base domain!")
