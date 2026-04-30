"""Permission classes for UniMarket."""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsEmailVerified(BasePermission):
    """
    Check if user has verified their email.
    """
    message = 'Email verification required.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Allow read-only methods for unverified users
        if request.method in SAFE_METHODS:
            return True
        
        # Check if email is verified
        try:
            email_address = request.user.emailaddress_set.get(primary=True)
            return email_address.verified
        except Exception:
            return False


class IsShopOwner(BasePermission):
    """
    Check if user owns the shop.
    """
    message = 'You do not own this shop.'

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsShopSeller(BasePermission):
    """
    Check if user is a seller in a shop (owner or staff).
    """
    message = 'You are not a seller in this shop.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ['seller', 'superadmin', 'university_admin', 'area_admin']


class IsUniversityAdmin(BasePermission):
    """
    Check if user is a university administrator.
    """
    message = 'You are not a university administrator.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ['university_admin', 'superadmin']


class IsLocationManager(BasePermission):
    """
    Check if user is a location/area manager.
    """
    message = 'You are not a location manager.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ['area_admin', 'superadmin']


class IsSuperAdmin(BasePermission):
    """
    Check if user is a superadmin.
    """
    message = 'Admin access required.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role == 'superadmin'


class IsBuyerOrSeller(BasePermission):
    """
    Check if user is a buyer or seller.
    """
    message = 'Buyer or seller access required.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ['buyer', 'seller', 'superadmin', 'university_admin', 'area_admin']


class CanModifyCatalogue(BasePermission):
    """
    Check if user can modify listings/catalogue.
    Sellers and admins only.
    """
    message = 'You do not have permission to modify listings.'

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.role in ['seller', 'superadmin', 'university_admin', 'area_admin']
