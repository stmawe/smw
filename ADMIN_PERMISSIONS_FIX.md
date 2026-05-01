# Admin User Permissions Fix

## Problem
The 'admins' user was unable to access `/console/domains/` endpoint because:

1. **Missing Superuser Status**: The 'admins' user was NOT set as a superuser (`is_superuser=False`)
2. **RBAC Permission Blocking**: The view decorator `@permission_required(AdminPermission.MANAGE_SHOP_DOMAINS)` checks permissions
3. **Permission Logic**: AdminPermissions class checks `user.is_superuser` FIRST before checking admin_role

## Root Cause
In `app/admin_permissions.py` AdminPermissions class:
```python
@property
def role(self):
    """Get user's admin role"""
    if self.user.is_superuser:
        self._role = AdminRole.SUPERUSER  # ✓ Gets ALL permissions
    elif hasattr(self.user, 'admin_role'):
        self._role = self.user.admin_role
    else:
        self._role = None
```

The 'admins' user was not a superuser, so permissions system couldn't grant them access to MANAGE_SHOP_DOMAINS permission.

## Solution

### Option 1: Quick Fix on Production
Run this command on the production server:
```bash
cd /usr/home/wiptech/domains/smw.pgwiz.cloud/public_python
python manage.py fix_admin_permissions
```

This will:
- Find the 'admins' user
- Set `is_superuser=True`
- Set `is_staff=True`
- Update the user in database

### Option 2: Use Seed Command (Full Reset)
```bash
python manage.py seed_admins
```

This creates/updates admin users with correct permissions.

### Option 3: Direct SQL Update
```sql
UPDATE auth_user SET is_superuser=true, is_staff=true WHERE username='admins';
```

## What Changed in Code

### 1. New Management Command: `fix_admin_permissions.py`
- Specific command to fix admin user permissions
- Safe to run multiple times
- Checks what needs to be updated before saving

### 2. Updated: `seed_admins.py`
- Previously didn't update `is_superuser`/`is_staff` for existing users
- Now properly updates these flags when re-running seed

### 3. Understanding Admin Permission Hierarchy

**Superuser (is_superuser=True)**
- Bypasses all permission checks
- Gets ALL admin permissions automatically
- No need for admin_role field

**Admin with AdminRole**
- Requires `admin_role` attribute
- Gets permissions based on role (Admin/Moderator/Support/Viewer)
- Still need `is_staff=True`

## Testing

After running the fix, test in Django shell:
```python
from app.models import User
from app.admin_permissions import AdminPermissions

u = User.objects.get(username='admins')
perms = AdminPermissions(u)

print(f'Is Superuser: {u.is_superuser}')  # Should be True
print(f'Admin Role: {perms.role}')  # Should be AdminRole.SUPERUSER
print(f'Can Manage Shop Domains: {perms.has("admin:manage_shop_domains")}')  # Should be True
```

## Files Modified
- `app/management/commands/fix_admin_permissions.py` - NEW
- `app/management/commands/seed_admins.py` - UPDATED
- `app/admin_permissions.py` - Already correct (no changes needed)

## Prevention
Always run `seed_admins` as part of deployment initialization to ensure admin users are properly seeded with correct permissions.
