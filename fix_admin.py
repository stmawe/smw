import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(__file__))

django.setup()

from app.models import User
from app.admin_permissions import AdminPermissions

# Get the admins user
u = User.objects.get(username='admins')
print(f'Current state:')
print(f'  User: {u}')
print(f'  Is Superuser: {u.is_superuser}')
print(f'  Is Staff: {u.is_staff}')

# Make them a superuser
u.is_superuser = True
u.is_staff = True
u.save()

# Verify permissions
perms = AdminPermissions(u)
print(f'\nAfter update:')
print(f'  User: {u}')
print(f'  Is Superuser: {u.is_superuser}')
print(f'  Is Staff: {u.is_staff}')
print(f'  Admin Role: {perms.role}')
print(f'  Can Manage Shops: {perms.can_manage_shops()}')
print(f'  Can Manage Shop Domains: {perms.has("admin:manage_shop_domains")}')
