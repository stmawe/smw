#!/usr/bin/env python
"""Verify admin user exists and can authenticate."""

import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')
django.setup()

from django.contrib.auth import get_user_model, authenticate

User = get_user_model()

# Check admin user exists
admin = User.objects.filter(username='admins').first()
if admin:
    print(f'✓ Admin user exists')
    print(f'  Username: {admin.username}')
    print(f'  Email: {admin.email}')
    print(f'  Is Staff: {admin.is_staff}')
    print(f'  Is Superuser: {admin.is_superuser}')
    print(f'  Password check: {admin.check_password("haha6admin")}')
    
    # Test authentication
    print('\nTesting authentication...')
    user_by_username = authenticate(username='admins', password='haha6admin')
    if user_by_username:
        print(f'✓ Authentication by username works')
    else:
        print(f'✗ Authentication by username FAILED')
    
    user_by_email = authenticate(username='admin@smw.pgwiz.cloud', password='haha6admin')
    if user_by_email:
        print(f'✓ Authentication by email works')
    else:
        print(f'✗ Authentication by email FAILED')
else:
    print(f'✗ Admin user NOT found')
