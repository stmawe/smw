#!/usr/bin/env python
"""Create admin test users"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Create superuser for testing
user, created = User.objects.get_or_create(
    username='admin_test',
    defaults={
        'email': 'admin@test.local',
        'is_staff': True,
        'is_superuser': True,
        'is_active': True,
    }
)

if created:
    user.set_password('admin_test_password')
    user.save()
    print(f"✓ Created admin user: admin_test / admin_test_password")
else:
    user.set_password('admin_test_password')
    user.save()
    print(f"✓ Updated admin user: admin_test / admin_test_password")

# Show all admin users
print(f"\nAdmin users in database:")
for u in User.objects.filter(is_staff=True):
    print(f"  - {u.username} (superuser={u.is_superuser})")
