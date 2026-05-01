"""
Comprehensive RBAC Permission Framework for Admin Panel

Defines role hierarchy, permissions, and permission checking utilities.
Roles: Superuser > Admin > Moderator > Support > Viewer

Permission Matrix:
- Superuser: All permissions (implicit)
- Admin: Create/edit/delete users/shops/listings/transactions/settings; moderate content
- Moderator: Moderate content (flag/approve/reject), view analytics (read-only)
- Support: View users/shops/listings, limited user support actions, read-only access
- Viewer: Read-only access to dashboards and reports

Usage:
    @permission_required('admin:manage_users')
    def manage_users_view(request):
        # Only admins and superusers can access
        pass

    if request.admin_perms.can('admin:manage_shops'):
        # Show edit button
"""

from enum import Enum
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.shortcuts import redirect


class AdminRole(Enum):
    """Admin role hierarchy"""
    SUPERUSER = 'superuser'  # System owner, full access
    ADMIN = 'admin'  # Full platform control (except billing)
    MODERATOR = 'moderator'  # Content moderation, reporting
    SUPPORT = 'support'  # User support, limited editing
    VIEWER = 'viewer'  # Read-only analytics and reports


class AdminPermission:
    """
    Permission constants organized by resource.
    Format: 'resource:action'
    """
    
    # User Management
    MANAGE_USERS = 'admin:manage_users'  # Create, edit, delete, suspend users
    VIEW_USERS = 'admin:view_users'  # View user list and details
    MANAGE_USER_ROLES = 'admin:manage_user_roles'  # Assign admin roles
    DELETE_USERS = 'admin:delete_users'  # Permanently delete users
    SUSPEND_USERS = 'admin:suspend_users'  # Suspend/activate users
    MANAGE_PASSWORDS = 'admin:manage_passwords'  # Change user passwords
    
    # Shop Management
    MANAGE_SHOPS = 'admin:manage_shops'  # Create, edit, delete shops
    VIEW_SHOPS = 'admin:view_shops'  # View shop list and details
    ACTIVATE_SHOPS = 'admin:activate_shops'  # Activate/deactivate shops
    DELETE_SHOPS = 'admin:delete_shops'  # Permanently delete shops
    MANAGE_SHOP_DOMAINS = 'admin:manage_shop_domains'  # Edit domains and SSL
    MANAGE_SHOP_THEMES = 'admin:manage_shop_themes'  # Change shop themes
    
    # Listing Management
    MANAGE_LISTINGS = 'admin:manage_listings'  # Edit/delete any listing
    VIEW_LISTINGS = 'admin:view_listings'  # View all listings
    FEATURE_LISTINGS = 'admin:feature_listings'  # Feature/unfeature listings
    DELETE_LISTINGS = 'admin:delete_listings'  # Permanently delete listings
    
    # Content Moderation
    MODERATE_CONTENT = 'admin:moderate_content'  # Flag, approve, reject content
    VIEW_FLAGS = 'admin:view_flags'  # View flagged content and reports
    BAN_USERS = 'admin:ban_users'  # Ban users from platform
    DELETE_COMMENTS = 'admin:delete_comments'  # Remove messages/comments
    
    # Transactions & Payments
    MANAGE_TRANSACTIONS = 'admin:manage_transactions'  # View and refund transactions
    VIEW_TRANSACTIONS = 'admin:view_transactions'  # View transaction history
    REFUND_TRANSACTIONS = 'admin:refund_transactions'  # Issue refunds
    MANUAL_PAYMENT = 'admin:manual_payment'  # Record manual payments
    
    # Categories & Catalog
    MANAGE_CATEGORIES = 'admin:manage_categories'  # Create/edit/delete categories
    VIEW_CATEGORIES = 'admin:view_categories'  # View categories
    
    # Site Settings
    MANAGE_SETTINGS = 'admin:manage_settings'  # Change site-wide settings
    MANAGE_EMAIL_CONFIG = 'admin:manage_email_config'  # SMTP configuration
    MANAGE_PAYMENT_CONFIG = 'admin:manage_payment_config'  # Payment gateway config
    MANAGE_SSL_CONFIG = 'admin:manage_ssl_config'  # SSL settings
    MANAGE_RATE_LIMITS = 'admin:manage_rate_limits'  # Rate limiting rules
    MANAGE_API_KEYS = 'admin:manage_api_keys'  # Generate/revoke API keys
    
    # Themes & Design
    MANAGE_THEMES = 'admin:manage_themes'  # Create/edit/delete themes
    MANAGE_DESIGN_TOKENS = 'admin:manage_design_tokens'  # Edit design tokens
    
    # Analytics & Reporting
    VIEW_ANALYTICS = 'admin:view_analytics'  # View analytics dashboard
    VIEW_REPORTS = 'admin:view_reports'  # Access reports
    EXPORT_DATA = 'admin:export_data'  # Export data to CSV/PDF
    
    # Audit & Security
    VIEW_AUDIT_LOGS = 'admin:view_audit_logs'  # View admin action logs
    MANAGE_ADMINS = 'admin:manage_admins'  # Invite/manage admin team
    MANAGE_SECURITY = 'admin:manage_security'  # Security settings (2FA, IP whitelist)
    
    # Tenant Management
    MANAGE_TENANTS = 'admin:manage_tenants'  # Create/edit tenants (multi-tenant only)
    MANAGE_BILLING = 'admin:manage_billing'  # Manage customer billing
    
    # System
    ACCESS_ADMIN_PANEL = 'admin:access_admin_panel'  # Access admin panel at all


# Permission matrix: role -> list of permissions
ROLE_PERMISSIONS = {
    AdminRole.SUPERUSER: 'all',  # Special: has all permissions
    
    AdminRole.ADMIN: [
        # Users
        AdminPermission.MANAGE_USERS,
        AdminPermission.VIEW_USERS,
        AdminPermission.MANAGE_USER_ROLES,
        AdminPermission.DELETE_USERS,
        AdminPermission.SUSPEND_USERS,
        AdminPermission.MANAGE_PASSWORDS,
        # Shops
        AdminPermission.MANAGE_SHOPS,
        AdminPermission.VIEW_SHOPS,
        AdminPermission.ACTIVATE_SHOPS,
        AdminPermission.DELETE_SHOPS,
        AdminPermission.MANAGE_SHOP_DOMAINS,
        AdminPermission.MANAGE_SHOP_THEMES,
        # Listings
        AdminPermission.MANAGE_LISTINGS,
        AdminPermission.VIEW_LISTINGS,
        AdminPermission.FEATURE_LISTINGS,
        AdminPermission.DELETE_LISTINGS,
        # Moderation
        AdminPermission.MODERATE_CONTENT,
        AdminPermission.VIEW_FLAGS,
        AdminPermission.BAN_USERS,
        AdminPermission.DELETE_COMMENTS,
        # Transactions
        AdminPermission.MANAGE_TRANSACTIONS,
        AdminPermission.VIEW_TRANSACTIONS,
        AdminPermission.REFUND_TRANSACTIONS,
        AdminPermission.MANUAL_PAYMENT,
        # Categories
        AdminPermission.MANAGE_CATEGORIES,
        AdminPermission.VIEW_CATEGORIES,
        # Settings
        AdminPermission.MANAGE_SETTINGS,
        AdminPermission.MANAGE_EMAIL_CONFIG,
        AdminPermission.MANAGE_PAYMENT_CONFIG,
        AdminPermission.MANAGE_SSL_CONFIG,
        AdminPermission.MANAGE_RATE_LIMITS,
        AdminPermission.MANAGE_API_KEYS,
        # Themes
        AdminPermission.MANAGE_THEMES,
        AdminPermission.MANAGE_DESIGN_TOKENS,
        # Analytics
        AdminPermission.VIEW_ANALYTICS,
        AdminPermission.VIEW_REPORTS,
        AdminPermission.EXPORT_DATA,
        # Audit
        AdminPermission.VIEW_AUDIT_LOGS,
        AdminPermission.MANAGE_ADMINS,
        AdminPermission.MANAGE_SECURITY,
        # Tenant
        AdminPermission.MANAGE_TENANTS,
        AdminPermission.MANAGE_BILLING,
        # System
        AdminPermission.ACCESS_ADMIN_PANEL,
    ],
    
    AdminRole.MODERATOR: [
        # Listings (read-only view + moderation)
        AdminPermission.VIEW_LISTINGS,
        AdminPermission.MODERATE_CONTENT,
        AdminPermission.VIEW_FLAGS,
        AdminPermission.BAN_USERS,
        AdminPermission.DELETE_COMMENTS,
        # Users (read-only view)
        AdminPermission.VIEW_USERS,
        # Shops (read-only view)
        AdminPermission.VIEW_SHOPS,
        # Analytics (read-only)
        AdminPermission.VIEW_ANALYTICS,
        AdminPermission.VIEW_REPORTS,
        # System
        AdminPermission.ACCESS_ADMIN_PANEL,
    ],
    
    AdminRole.SUPPORT: [
        # Users (view + limited support actions)
        AdminPermission.VIEW_USERS,
        AdminPermission.SUSPEND_USERS,
        # Shops (view only)
        AdminPermission.VIEW_SHOPS,
        # Listings (view only)
        AdminPermission.VIEW_LISTINGS,
        # Transactions (view only)
        AdminPermission.VIEW_TRANSACTIONS,
        # Categories (view only)
        AdminPermission.VIEW_CATEGORIES,
        # Analytics
        AdminPermission.VIEW_ANALYTICS,
        AdminPermission.VIEW_REPORTS,
        AdminPermission.EXPORT_DATA,
        # System
        AdminPermission.ACCESS_ADMIN_PANEL,
    ],
    
    AdminRole.VIEWER: [
        # Read-only access to everything
        AdminPermission.VIEW_USERS,
        AdminPermission.VIEW_SHOPS,
        AdminPermission.VIEW_LISTINGS,
        AdminPermission.VIEW_TRANSACTIONS,
        AdminPermission.VIEW_CATEGORIES,
        AdminPermission.VIEW_FLAGS,
        AdminPermission.VIEW_ANALYTICS,
        AdminPermission.VIEW_REPORTS,
        AdminPermission.EXPORT_DATA,
        AdminPermission.VIEW_AUDIT_LOGS,
        # System
        AdminPermission.ACCESS_ADMIN_PANEL,
    ],
}


class AdminPermissions:
    """
    Permission checker for admin users.
    Attached to request object by middleware.
    """
    
    def __init__(self, user):
        self.user = user
        self._role = None
        self._permissions = None
    
    @property
    def role(self):
        """Get user's admin role"""
        if self._role is None:
            if self.user.is_superuser:
                self._role = AdminRole.SUPERUSER
            elif hasattr(self.user, 'admin_role'):
                self._role = self.user.admin_role
            else:
                self._role = None
        return self._role
    
    def get_permissions(self):
        """Get list of permissions for user's role"""
        if self._permissions is not None:
            return self._permissions
        
        role = self.role
        if role is None:
            self._permissions = []
        elif role == AdminRole.SUPERUSER:
            # Superuser has all permissions
            self._permissions = [
                perm for perm in dir(AdminPermission)
                if not perm.startswith('_') and perm.isupper()
            ]
        else:
            self._permissions = ROLE_PERMISSIONS.get(role, [])
        
        return self._permissions
    
    def has(self, permission):
        """Check if user has specific permission"""
        if not self.user.is_authenticated:
            return False
        
        if self.user.is_superuser:
            return True
        
        permissions = self.get_permissions()
        return permission in permissions
    
    def has_any(self, permissions):
        """Check if user has any of the specified permissions"""
        return any(self.has(perm) for perm in permissions)
    
    def has_all(self, permissions):
        """Check if user has all specified permissions"""
        return all(self.has(perm) for perm in permissions)
    
    def can_manage_users(self):
        """Shortcut: check if user can manage users"""
        return self.has(AdminPermission.MANAGE_USERS)
    
    def can_manage_shops(self):
        """Shortcut: check if user can manage shops"""
        return self.has(AdminPermission.MANAGE_SHOPS)
    
    def can_manage_listings(self):
        """Shortcut: check if user can manage listings"""
        return self.has(AdminPermission.MANAGE_LISTINGS)
    
    def can_moderate(self):
        """Shortcut: check if user can moderate content"""
        return self.has(AdminPermission.MODERATE_CONTENT)
    
    def can_manage_transactions(self):
        """Shortcut: check if user can manage transactions"""
        return self.has(AdminPermission.MANAGE_TRANSACTIONS)
    
    def can_manage_settings(self):
        """Shortcut: check if user can manage site settings"""
        return self.has(AdminPermission.MANAGE_SETTINGS)
    
    def can_view_analytics(self):
        """Shortcut: check if user can view analytics"""
        return self.has(AdminPermission.VIEW_ANALYTICS)
    
    def __repr__(self):
        return f"AdminPermissions(role={self.role}, user={self.user.username})"


def permission_required(permission, redirect_to='admin_login'):
    """
    Decorator to require specific permission for a view.
    
    Usage:
        @permission_required('admin:manage_users')
        def manage_users_view(request):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url=redirect_to)
        def wrapper(request, *args, **kwargs):
            # Check if user has admin access
            if not hasattr(request, 'admin_perms'):
                return HttpResponseForbidden('Admin access required')
            
            # Check specific permission
            if not request.admin_perms.has(permission):
                messages.error(request, 'You do not have permission to access this page.')
                return redirect(redirect_to)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def role_required(role, redirect_to='admin_login'):
    """
    Decorator to require specific admin role.
    
    Usage:
        @role_required(AdminRole.ADMIN)
        def admin_dashboard_view(request):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url=redirect_to)
        def wrapper(request, *args, **kwargs):
            if not hasattr(request, 'admin_perms'):
                return HttpResponseForbidden('Admin access required')
            
            user_role = request.admin_perms.role
            if user_role != role and user_role != AdminRole.SUPERUSER:
                messages.error(request, f'This page requires {role.value} role.')
                return redirect(redirect_to)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def admin_access_required(redirect_to='admin_login'):
    """
    Decorator to require any admin access (just checks ACCESS_ADMIN_PANEL permission).
    More lenient than permission_required for general admin pages.
    
    Usage:
        @admin_access_required()
        def admin_dashboard_view(request):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url=redirect_to)
        def wrapper(request, *args, **kwargs):
            if not hasattr(request, 'admin_perms'):
                messages.error(request, 'Admin access required')
                return redirect(redirect_to)
            
            if not request.admin_perms.has(AdminPermission.ACCESS_ADMIN_PANEL):
                messages.error(request, 'You do not have admin access.')
                return redirect(redirect_to)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
