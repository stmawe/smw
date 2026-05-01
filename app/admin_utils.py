"""
Admin Utility Functions & Helpers
Common functions used across admin views.
"""

from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
import csv
from io import StringIO
from django.http import HttpResponse

from .models import AdminAuditLog, AdminActivityFeed
from mydak.models import Shop, Listing, Transaction


# ============================================================
# FILTERING & SEARCH UTILITIES
# ============================================================

def filter_users(queryset, search=None, role=None, is_staff=None, is_active=None):
    """Apply common user filters."""
    if search:
        queryset = queryset.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    if role:
        queryset = queryset.filter(role=role)
    if is_staff is not None:
        queryset = queryset.filter(is_staff=is_staff)
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)
    
    return queryset


def filter_shops(queryset, search=None, is_active=None):
    """Apply common shop filters."""
    if search:
        queryset = queryset.filter(Q(name__icontains=search))
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)
    
    return queryset


def filter_listings(queryset, search=None, status=None, is_featured=None):
    """Apply common listing filters."""
    if search:
        queryset = queryset.filter(Q(title__icontains=search))
    if status:
        queryset = queryset.filter(status=status)
    if is_featured is not None:
        queryset = queryset.filter(is_featured=is_featured)
    
    return queryset


def filter_transactions(queryset, status=None, date_from=None, date_to=None):
    """Apply common transaction filters."""
    if status:
        queryset = queryset.filter(status=status)
    if date_from:
        queryset = queryset.filter(created_at__gte=date_from)
    if date_to:
        queryset = queryset.filter(created_at__lte=date_to)
    
    return queryset


# ============================================================
# STATISTICS & ANALYTICS
# ============================================================

def get_dashboard_stats():
    """Get comprehensive dashboard statistics."""
    from .models import User
    
    total_users = User.objects.count()
    total_shops = Shop.objects.count()
    total_listings = Listing.objects.count()
    total_transactions = Transaction.objects.count()
    
    week_ago = timezone.now() - timedelta(days=7)
    month_ago = timezone.now() - timedelta(days=30)
    
    new_users_week = User.objects.filter(date_joined__gte=week_ago).count()
    new_shops_week = Shop.objects.filter(created_at__gte=week_ago).count() if hasattr(Shop, 'created_at') else 0
    
    transactions_week = Transaction.objects.filter(created_at__gte=week_ago)
    revenue_week = sum(float(t.amount) for t in transactions_week if hasattr(t, 'amount'))
    
    pending_listings = Listing.objects.filter(status='pending').count() if hasattr(Listing, 'status') else 0
    
    return {
        'total_users': total_users,
        'total_shops': total_shops,
        'total_listings': total_listings,
        'total_transactions': total_transactions,
        'new_users_week': new_users_week,
        'new_shops_week': new_shops_week,
        'revenue_week': revenue_week,
        'pending_listings': pending_listings,
    }


def get_user_stats(user):
    """Get statistics for a specific user."""
    from .models import User
    
    shops = Shop.objects.filter(owner=user).count() if hasattr(Shop, 'owner') else 0
    listings = Listing.objects.filter(shop__owner=user).count() if hasattr(Listing, 'shop') else 0
    transactions = Transaction.objects.filter(seller=user).count() if hasattr(Transaction, 'seller') else 0
    
    joined_days = (timezone.now() - user.date_joined).days
    
    return {
        'shops': shops,
        'listings': listings,
        'transactions': transactions,
        'joined_days': joined_days,
        'is_active': user.is_active,
        'is_staff': user.is_staff,
    }


def get_shop_stats(shop):
    """Get statistics for a specific shop."""
    listings = Listing.objects.filter(shop=shop)
    total_listings = listings.count()
    active_listings = listings.filter(is_active=True).count() if hasattr(Listing, 'is_active') else 0
    
    transactions = Transaction.objects.filter(shop=shop)
    total_revenue = sum(float(t.amount) for t in transactions if hasattr(t, 'amount'))
    
    return {
        'total_listings': total_listings,
        'active_listings': active_listings,
        'total_revenue': total_revenue,
        'transaction_count': transactions.count(),
    }


# ============================================================
# EXPORT & REPORTING
# ============================================================

def export_users_csv(queryset, fields=None):
    """Export users to CSV."""
    if fields is None:
        fields = ['id', 'username', 'email', 'is_staff', 'is_active', 'role', 'date_joined']
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(fields)
    
    for user in queryset:
        row = [str(getattr(user, field, '')) for field in fields]
        writer.writerow(row)
    
    return response


def export_shops_csv(queryset, fields=None):
    """Export shops to CSV."""
    if fields is None:
        fields = ['id', 'name', 'owner_id', 'is_active', 'created_at']
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="shops_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(fields)
    
    for shop in queryset:
        row = []
        for field in fields:
            if field == 'owner_id':
                value = shop.owner.id if hasattr(shop, 'owner') else ''
            else:
                value = getattr(shop, field, '')
            row.append(str(value))
        writer.writerow(row)
    
    return response


def export_transactions_csv(queryset, fields=None):
    """Export transactions to CSV."""
    if fields is None:
        fields = ['id', 'transaction_id', 'seller_id', 'buyer_id', 'amount', 'status', 'created_at']
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(fields)
    
    for transaction in queryset:
        row = []
        for field in fields:
            if field == 'seller_id':
                value = transaction.seller.id if hasattr(transaction, 'seller') else ''
            elif field == 'buyer_id':
                value = transaction.buyer.id if hasattr(transaction, 'buyer') else ''
            else:
                value = getattr(transaction, field, '')
            row.append(str(value))
        writer.writerow(row)
    
    return response


# ============================================================
# AUDIT LOG HELPERS
# ============================================================

def get_audit_logs_for_object(content_type, object_id, limit=50):
    """Get all audit logs for a specific object."""
    return AdminAuditLog.objects.filter(
        content_type=content_type,
        object_id=str(object_id)
    ).order_by('-created_at')[:limit]


def get_admin_activity_summary(days=30):
    """Get summary of admin activity over time period."""
    start_date = timezone.now() - timedelta(days=days)
    
    logs = AdminAuditLog.objects.filter(created_at__gte=start_date)
    
    summary = {
        'total_actions': logs.count(),
        'by_action': dict(logs.values('action').annotate(count=Count('*')).values_list('action', 'count')),
        'by_admin': dict(logs.values('admin_username').annotate(count=Count('*')).values_list('admin_username', 'count')),
        'by_content_type': dict(logs.values('content_type').annotate(count=Count('*')).values_list('content_type', 'count')),
        'errors': logs.filter(status='error').count(),
    }
    
    return summary


# ============================================================
# VALIDATION & BUSINESS LOGIC
# ============================================================

def can_delete_category(category):
    """Check if category can be safely deleted."""
    listing_count = Listing.objects.filter(category=category).count()
    return listing_count == 0


def can_delete_shop(shop):
    """Check if shop can be safely deleted."""
    listing_count = Listing.objects.filter(shop=shop).count()
    transaction_count = Transaction.objects.filter(shop=shop).count()
    return listing_count == 0 and transaction_count == 0


def validate_user_email(email):
    """Validate email is not already used."""
    from .models import User
    
    return not User.objects.filter(email=email).exists()


def get_permission_description(permission_code):
    """Get human-readable description of a permission."""
    descriptions = {
        'admin:manage_users': 'Create, edit, delete, and manage user accounts',
        'admin:manage_shops': 'Create, edit, delete, and manage shop operations',
        'admin:manage_listings': 'Edit, delete, feature, and manage listings',
        'admin:moderate_content': 'Flag, approve, and reject user content',
        'admin:manage_transactions': 'View and manage transaction history',
        'admin:manage_settings': 'Change site-wide settings and configuration',
        'admin:view_audit_logs': 'View audit logs of admin actions',
        'admin:access_admin_panel': 'Access the admin panel',
    }
    return descriptions.get(permission_code, permission_code)


# ============================================================
# CACHE & PERFORMANCE
# ============================================================

# ============================================================
# CACHE & PERFORMANCE
# ============================================================

# Cache timeout constants (in seconds)
CACHE_TIMEOUT_SHORT = 300  # 5 minutes
CACHE_TIMEOUT_MEDIUM = 1800  # 30 minutes
CACHE_TIMEOUT_LONG = 3600  # 1 hour

# Cache key registry
CACHE_KEYS = {
    # Dashboard
    'admin:dashboard_stats': CACHE_TIMEOUT_MEDIUM,
    'admin:dashboard_metrics': CACHE_TIMEOUT_SHORT,
    
    # User data
    'admin:users_list': CACHE_TIMEOUT_MEDIUM,
    'admin:user_roles': CACHE_TIMEOUT_LONG,
    'admin:user:%(user_id)s:stats': CACHE_TIMEOUT_SHORT,
    
    # Shop data
    'admin:shops_list': CACHE_TIMEOUT_MEDIUM,
    'admin:shop:%(shop_id)s:stats': CACHE_TIMEOUT_SHORT,
    'admin:shop:%(shop_id)s:listings': CACHE_TIMEOUT_MEDIUM,
    
    # Category data
    'admin:categories_list': CACHE_TIMEOUT_LONG,
    'admin:category:%(category_id)s:count': CACHE_TIMEOUT_MEDIUM,
    
    # Configuration
    'admin:settings': CACHE_TIMEOUT_LONG,
    'admin:active_theme': CACHE_TIMEOUT_LONG,
    'admin:active_theme_css': CACHE_TIMEOUT_LONG,
    'admin:payment_config': CACHE_TIMEOUT_LONG,
    'admin:email_config': CACHE_TIMEOUT_LONG,
    
    # Analytics
    'admin:analytics:top_sellers': CACHE_TIMEOUT_MEDIUM,
    'admin:analytics:revenue': CACHE_TIMEOUT_SHORT,
    'admin:analytics:growth': CACHE_TIMEOUT_SHORT,
    
    # Reports
    'admin:report:%(report_id)s': CACHE_TIMEOUT_MEDIUM,
    'admin:activity_feed': CACHE_TIMEOUT_SHORT,
    
    # Permissions
    'admin:permission_matrix': CACHE_TIMEOUT_LONG,
}


def clear_admin_cache(pattern=None):
    """Clear cached data for admin panel."""
    from django.core.cache import cache
    
    if pattern:
        # Clear specific pattern (e.g., 'admin:shop:*')
        from django.core.cache import caches
        try:
            # Django's default cache doesn't support pattern deletion
            # but this works for memcached and redis
            cache.delete_pattern(pattern)
        except (AttributeError, NotImplementedError):
            # Fallback: clear specific keys
            import fnmatch
            for key in CACHE_KEYS.keys():
                if fnmatch.fnmatch(key, pattern):
                    cache.delete(key)
    else:
        # Clear all admin cache keys
        for key in CACHE_KEYS.keys():
            # Skip template-based keys (they're not cached directly)
            if '%' not in key:
                cache.delete(key)


def get_cached_dashboard_stats(timeout=None):
    """Get dashboard stats with intelligent caching."""
    from django.core.cache import cache
    
    cache_key = 'admin:dashboard_stats'
    timeout = timeout or CACHE_KEYS[cache_key]
    
    stats = cache.get(cache_key)
    
    if stats is None:
        stats = get_dashboard_stats()
        cache.set(cache_key, stats, timeout)
    
    return stats


def get_cached_users_list(filters=None, timeout=None):
    """Get cached users list (with optional filters)."""
    from django.core.cache import cache
    from .models import User
    
    cache_key = f'admin:users_list:{str(filters) if filters else "all"}'
    timeout = timeout or CACHE_TIMEOUT_MEDIUM
    
    users = cache.get(cache_key)
    
    if users is None:
        users = User.objects.all()
        if filters:
            users = filter_users(users, **filters)
        users = list(users.values('id', 'username', 'email', 'is_staff', 'is_active', 'role'))
        cache.set(cache_key, users, timeout)
    
    return users


def get_cached_shops_list(filters=None, timeout=None):
    """Get cached shops list with filter support."""
    from django.core.cache import cache
    
    cache_key = f'admin:shops_list:{str(filters) if filters else "all"}'
    timeout = timeout or CACHE_TIMEOUT_MEDIUM
    
    shops = cache.get(cache_key)
    
    if shops is None:
        shops = Shop.objects.select_related('owner')
        if filters:
            shops = filter_shops(shops, **filters)
        shops = list(shops.values('id', 'name', 'owner_id', 'is_active', 'has_ssl'))
        cache.set(cache_key, shops, timeout)
    
    return shops


def get_cached_categories_list(timeout=None):
    """Get cached categories list."""
    from django.core.cache import cache
    
    cache_key = 'admin:categories_list'
    timeout = timeout or CACHE_TIMEOUT_LONG
    
    categories = cache.get(cache_key)
    
    if categories is None:
        from .models import Category
        categories = list(Category.objects.values('id', 'name', 'icon', 'description'))
        cache.set(cache_key, categories, timeout)
    
    return categories


def get_cached_active_theme(timeout=None):
    """Get cached active theme configuration."""
    from django.core.cache import cache
    
    cache_key = 'admin:active_theme'
    timeout = timeout or CACHE_TIMEOUT_LONG
    
    theme = cache.get(cache_key)
    
    if theme is None:
        from .models import Theme
        try:
            theme = Theme.objects.filter(is_active=True).first()
            if theme:
                theme = {
                    'id': theme.id,
                    'name': theme.name,
                    'primary_color': theme.primary_color,
                    'secondary_color': theme.secondary_color,
                }
            cache.set(cache_key, theme, timeout)
        except Exception:
            pass
    
    return theme


def get_cached_theme_css(theme_id, timeout=None):
    """Get cached compiled theme CSS."""
    from django.core.cache import cache
    
    cache_key = f'admin:theme:{theme_id}:css'
    timeout = timeout or CACHE_TIMEOUT_LONG
    
    css = cache.get(cache_key)
    
    if css is None:
        from .models import Theme
        try:
            theme = Theme.objects.get(id=theme_id)
            # Compile theme CSS from tokens
            css = theme.compile_css() if hasattr(theme, 'compile_css') else ''
            cache.set(cache_key, css, timeout)
        except Exception:
            css = ''
    
    return css


def get_cached_settings(setting_key=None, timeout=None):
    """Get cached site settings."""
    from django.core.cache import cache
    
    if setting_key:
        cache_key = f'admin:setting:{setting_key}'
    else:
        cache_key = 'admin:settings'
    
    timeout = timeout or CACHE_TIMEOUT_LONG
    
    settings_data = cache.get(cache_key)
    
    if settings_data is None:
        # Fetch from database or config file
        # This is a placeholder - implement based on your settings model
        settings_data = {}
        cache.set(cache_key, settings_data, timeout)
    
    return settings_data


def get_cached_top_sellers(days=30, limit=10, timeout=None):
    """Get cached top sellers analytics."""
    from django.core.cache import cache
    
    cache_key = f'admin:analytics:top_sellers:{days}d'
    timeout = timeout or CACHE_TIMEOUT_MEDIUM
    
    sellers = cache.get(cache_key)
    
    if sellers is None:
        sellers = get_dashboard_stats().get('top_sellers', [])
        cache.set(cache_key, sellers, timeout)
    
    return sellers[:limit]


def get_cached_analytics_summary(days=30, timeout=None):
    """Get cached analytics summary."""
    from django.core.cache import cache
    
    cache_key = f'admin:analytics:summary:{days}d'
    timeout = timeout or CACHE_TIMEOUT_SHORT
    
    summary = cache.get(cache_key)
    
    if summary is None:
        start_date = timezone.now() - timedelta(days=days)
        
        summary = {
            'period_days': days,
            'total_revenue': 0,
            'new_users': User.objects.filter(date_joined__gte=start_date).count(),
            'new_shops': Shop.objects.filter(created_at__gte=start_date).count(),
            'new_listings': Listing.objects.filter(created_at__gte=start_date).count(),
            'total_transactions': Transaction.objects.filter(created_at__gte=start_date).count(),
        }
        
        # Calculate revenue
        if hasattr(Transaction, 'objects'):
            result = Transaction.objects.filter(
                created_at__gte=start_date
            ).aggregate(Count('id'))
            # Add actual revenue if amount field exists
        
        cache.set(cache_key, summary, timeout)
    
    return summary


def get_cached_permission_matrix(timeout=None):
    """Get cached permission matrix for all roles."""
    from django.core.cache import cache
    from .admin_permissions import ROLE_PERMISSIONS
    
    cache_key = 'admin:permission_matrix'
    timeout = timeout or CACHE_TIMEOUT_LONG
    
    matrix = cache.get(cache_key)
    
    if matrix is None:
        matrix = dict(ROLE_PERMISSIONS)
        cache.set(cache_key, matrix, timeout)
    
    return matrix


def invalidate_user_cache(user_id):
    """Invalidate cache for a specific user."""
    from django.core.cache import cache
    
    cache.delete(f'admin:user:{user_id}:stats')
    cache.delete(f'admin:users_list:all')
    # Clear all user list variations
    clear_admin_cache('admin:users_list:*')


def invalidate_shop_cache(shop_id):
    """Invalidate cache for a specific shop."""
    from django.core.cache import cache
    
    cache.delete(f'admin:shop:{shop_id}:stats')
    cache.delete(f'admin:shop:{shop_id}:listings')
    cache.delete(f'admin:shops_list:all')
    # Clear all shop list variations
    clear_admin_cache('admin:shops_list:*')
    # Clear analytics (may be affected)
    cache.delete('admin:analytics:top_sellers')


def invalidate_category_cache(category_id=None):
    """Invalidate cache for categories."""
    from django.core.cache import cache
    
    if category_id:
        cache.delete(f'admin:category:{category_id}:count')
    
    cache.delete('admin:categories_list')


def invalidate_theme_cache(theme_id=None):
    """Invalidate cache for theme."""
    from django.core.cache import cache
    
    if theme_id:
        cache.delete(f'admin:theme:{theme_id}:css')
    
    cache.delete('admin:active_theme')
    cache.delete('admin:active_theme_css')


def invalidate_analytics_cache():
    """Invalidate all analytics cache."""
    from django.core.cache import cache
    
    clear_admin_cache('admin:analytics:*')


def invalidate_dashboard_cache():
    """Invalidate dashboard and related caches."""
    from django.core.cache import cache
    
    cache.delete('admin:dashboard_stats')
    cache.delete('admin:dashboard_metrics')
    clear_admin_cache('admin:analytics:*')


def get_cache_stats():
    """Get cache performance statistics."""
    from django.core.cache import cache
    
    # This depends on cache backend (redis, memcached, etc.)
    # Returns stats like hits, misses, etc. if available
    try:
        if hasattr(cache, 'get_stats'):
            return cache.get_stats()
    except Exception:
        pass
    
    return {
        'backend': type(cache).__name__,
        'note': 'Cache statistics not available for this backend'
    }


# ============================================================
# SIGNAL HANDLERS FOR CACHE INVALIDATION
# ============================================================

def setup_cache_invalidation_signals():
    """
    Register Django signal handlers to invalidate cache on model changes.
    Should be called in apps.py ready() method.
    """
    from django.db.models.signals import post_save, post_delete
    from django.dispatch import receiver
    from .models import User, Theme
    from mydak.models import Shop, Listing, Transaction, Category
    
    @receiver(post_save, sender=User)
    def invalidate_user_on_save(sender, instance, **kwargs):
        invalidate_user_cache(instance.id)
        clear_admin_cache('admin:users_list:*')
    
    @receiver(post_delete, sender=User)
    def invalidate_user_on_delete(sender, instance, **kwargs):
        invalidate_user_cache(instance.id)
        clear_admin_cache('admin:users_list:*')
    
    @receiver(post_save, sender=Shop)
    def invalidate_shop_on_save(sender, instance, **kwargs):
        invalidate_shop_cache(instance.id)
    
    @receiver(post_delete, sender=Shop)
    def invalidate_shop_on_delete(sender, instance, **kwargs):
        invalidate_shop_cache(instance.id)
    
    @receiver(post_save, sender=Listing)
    @receiver(post_delete, sender=Listing)
    def invalidate_on_listing_change(sender, instance, **kwargs):
        invalidate_shop_cache(instance.shop.id if hasattr(instance, 'shop') else None)
        invalidate_analytics_cache()
    
    @receiver(post_save, sender=Theme)
    def invalidate_theme_on_save(sender, instance, **kwargs):
        invalidate_theme_cache(instance.id)
    
    @receiver(post_save, sender=Transaction)
    @receiver(post_delete, sender=Transaction)
    def invalidate_on_transaction_change(sender, instance, **kwargs):
        invalidate_analytics_cache()
        invalidate_dashboard_cache()
