#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smw.settings')
django.setup()

from django.urls import resolve, Resolver404
from app.admin_urls import admin_subdomain_patterns

print("✓ Testing URL resolution (without DB access):\n")

# Test URL resolution
test_urls = [
    '/admin/shops/',
    '/admin/shop/1/',
    '/admin/transactions/',
    '/admin/listings/',
    '/admin/analytics/',
    '/admin/users/',
]

for url_path in test_urls:
    try:
        match = resolve(url_path, urlconf='app.admin_urls')
        print(f"✓ {url_path:30} -> {match.func.__name__}")
    except Resolver404 as e:
        print(f"✗ {url_path:30} -> NOT FOUND")

# Check registered patterns
print(f"\n✓ Total patterns in admin_subdomain_patterns: {len(admin_subdomain_patterns)}")
print("\nRegistered patterns:")
for i, pattern in enumerate(admin_subdomain_patterns):
    print(f"  {i+1}. {pattern.pattern}")

