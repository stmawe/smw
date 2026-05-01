"""
RBAC Middleware for Admin Panel

Attaches admin permissions to request object and validates admin role requirements.
Cascades from is_staff/is_superuser to admin role system for backwards compatibility.
"""

from django.utils.deprecation import MiddlewareMixin
from app.admin_permissions import AdminPermissions, AdminRole


class AdminRolesMiddleware(MiddlewareMixin):
    """
    Middleware to attach admin permissions to request object.
    
    Attaches:
    - request.admin_perms: AdminPermissions instance for checking permissions
    - request.admin_role: Current admin role (or None if not admin)
    - request.is_admin: Boolean indicating if user has admin access
    
    Cascades from is_staff to admin roles:
    - is_superuser -> AdminRole.SUPERUSER
    - is_staff and no explicit role -> AdminRole.ADMIN
    """
    
    def process_request(self, request):
        """Attach permissions object to request"""
        request.admin_perms = None
        request.admin_role = None
        request.is_admin = False
        
        # If user is not authenticated, skip
        if not request.user.is_authenticated:
            return None
        
        # Cascade from Django's built-in permissions
        # This ensures backwards compatibility with existing is_staff/is_superuser checks
        if request.user.is_superuser or request.user.is_staff:
            # Create permissions object
            request.admin_perms = AdminPermissions(request.user)
            request.admin_role = request.admin_perms.role
            request.is_admin = True
            
            return None
        
        # Check if user has explicit admin_role (from future database field)
        if hasattr(request.user, 'admin_role') and request.user.admin_role:
            request.admin_perms = AdminPermissions(request.user)
            request.admin_role = request.user.admin_role
            request.is_admin = True
            
            return None
        
        return None


def get_admin_perms(request):
    """Utility to get admin permissions from request"""
    if not hasattr(request, 'admin_perms'):
        request.admin_perms = AdminPermissions(request.user) if request.user.is_authenticated else None
    return request.admin_perms
