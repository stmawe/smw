#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from app.models import AdminUser
from app.admin_permissions import AdminPermissions, AdminPermission

u = User.objects.filter(username='admins').first()
if u:
    print(f'User: {u}')
    print(f'Is Superuser: {u.is_superuser}')
    print(f'Is Staff: {u.is_staff}')
    
    # Check admin role
    admin_user = AdminUser.objects.filter(user=u).first()
    if admin_user:
        print(f'Admin Role: {admin_user.role}')
    else:
        print('No AdminUser record found')
    
    # Check permissions
    perms = AdminPermissions(u)
    print(f'Can Manage Shops: {perms.can_manage_shops()}')
    print(f'Can Manage Shop Domains: {perms.has(AdminPermission.MANAGE_SHOP_DOMAINS)}')
    print(f'All Permissions: {perms.get_permissions()[:5]}...')
else:
    print('User not found')
