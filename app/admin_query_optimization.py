"""
Admin Query Optimization Utilities
Optimizes database queries using select_related and prefetch_related
to eliminate N+1 query problems.
"""

from django.db.models import Prefetch, Q, Count, Sum
from django.utils import timezone
from datetime import timedelta

from .models import User, Theme, ThemeToken, AdminAuditLog, AdminActivityFeed
from mydak.models import Shop, Listing, Transaction, Category


# ============================================================
# OPTIMIZED QUERYSETS
# ============================================================

def get_optimized_users_queryset():
    """Get users with minimal database queries."""
    return User.objects.select_related().prefetch_related('shops').only(
        'id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 
        'is_active', 'role', 'date_joined'
    )


def get_optimized_shops_queryset():
    """Get shops with owner and stats in single query."""
    return Shop.objects.select_related('owner').prefetch_related(
        Prefetch(
            'listings',
            queryset=Listing.objects.filter(status='active').only('id', 'shop_id')
        )
    ).annotate(
        listing_count=Count('listings'),
        active_listing_count=Count('listings', filter=Q(listings__status='active'))
    ).only(
        'id', 'name', 'owner_id', 'is_active', 'has_ssl', 'ssl_expires_at', 'created_at'
    )


def get_optimized_listings_queryset():
    """Get listings with shop and category in single query."""
    return Listing.objects.select_related('shop', 'category').prefetch_related(
        Prefetch(
            'transaction_set',
            queryset=Transaction.objects.only('id', 'listing_id', 'amount')
        )
    ).annotate(
        sale_count=Count('transaction'),
        total_revenue=Sum('transaction__amount')
    ).only(
        'id', 'title', 'status', 'is_featured', 'shop_id', 'category_id', 'created_at', 'updated_at'
    )


def get_optimized_transactions_queryset():
    """Get transactions with related data."""
    return Transaction.objects.select_related('shop', 'shop__owner').only(
        'id', 'shop_id', 'amount', 'status', 'created_at', 'updated_at'
    )


def get_optimized_categories_queryset():
    """Get categories with listing counts."""
    return Category.objects.annotate(
        listing_count=Count('listing')
    ).only('id', 'name', 'icon', 'description')


def get_optimized_themes_queryset():
    """Get themes with creator info."""
    return Theme.objects.select_related('created_by').only(
        'id', 'name', 'description', 'is_active', 'is_public', 'created_by_id', 'created_at'
    )


def get_optimized_audit_logs_queryset(limit=100):
    """Get audit logs with admin user info."""
    return AdminAuditLog.objects.select_related('admin_user').only(
        'id', 'admin_user_id', 'admin_username', 'action', 'content_type', 
        'object_id', 'object_str', 'status', 'reason', 'created_at'
    ).order_by('-created_at')[:limit]


def get_optimized_activity_feed_queryset(limit=50):
    """Get activity feed with admin user info."""
    return AdminActivityFeed.objects.select_related('admin_user').only(
        'id', 'admin_user_id', 'activity_type', 'content_type', 'object_id',
        'object_title', 'description', 'icon', 'severity', 'created_at'
    ).order_by('-created_at')[:limit]


# ============================================================
# BATCH RETRIEVAL FUNCTIONS
# ============================================================

def get_users_batch(user_ids):
    """Get multiple users efficiently."""
    return get_optimized_users_queryset().filter(id__in=user_ids)


def get_shops_batch(shop_ids):
    """Get multiple shops efficiently."""
    return get_optimized_shops_queryset().filter(id__in=shop_ids)


def get_listings_batch(listing_ids):
    """Get multiple listings efficiently."""
    return get_optimized_listings_queryset().filter(id__in=listing_ids)


def get_shop_listings(shop_id, status=None):
    """Get all listings for a shop."""
    listings = Listing.objects.filter(shop_id=shop_id).select_related(
        'category'
    ).prefetch_related(
        Prefetch(
            'transaction_set',
            queryset=Transaction.objects.select_related('shop').only('id', 'amount', 'status')
        )
    )
    
    if status:
        listings = listings.filter(status=status)
    
    return listings.annotate(sale_count=Count('transaction'), total_revenue=Sum('transaction__amount'))


def get_shop_statistics(shop_id):
    """Get comprehensive shop statistics with minimal queries."""
    shop = Shop.objects.select_related('owner').get(id=shop_id)
    
    # Single query to get all stats
    listings = Listing.objects.filter(shop_id=shop_id).aggregate(
        total_listings=Count('id'),
        active_listings=Count('id', filter=Q(status='active')),
        featured_listings=Count('id', filter=Q(is_featured=True)),
    )
    
    transactions = Transaction.objects.filter(shop_id=shop_id).aggregate(
        total_transactions=Count('id'),
        total_revenue=Sum('amount'),
        pending_revenue=Sum('amount', filter=Q(status='pending')),
    )
    
    # Combine all stats
    stats = {
        'shop': shop,
        'listings': listings,
        'transactions': transactions,
    }
    
    return stats


def get_user_statistics(user_id):
    """Get comprehensive user statistics with minimal queries."""
    user = User.objects.get(id=user_id)
    
    # Batch queries for all user-related stats
    shops_stats = Shop.objects.filter(owner_id=user_id).aggregate(
        total_shops=Count('id'),
        active_shops=Count('id', filter=Q(is_active=True)),
    )
    
    # Get total listings across all user's shops
    user_shops = Shop.objects.filter(owner_id=user_id).values_list('id', flat=True)
    listings_stats = Listing.objects.filter(shop_id__in=user_shops).aggregate(
        total_listings=Count('id'),
        active_listings=Count('id', filter=Q(status='active')),
    )
    
    # Get total transactions
    transactions_stats = Transaction.objects.filter(shop_id__in=user_shops).aggregate(
        total_transactions=Count('id'),
        total_revenue=Sum('amount'),
    )
    
    stats = {
        'user': user,
        'shops': shops_stats,
        'listings': listings_stats,
        'transactions': transactions_stats,
    }
    
    return stats


def get_dashboard_stats_optimized():
    """Get all dashboard statistics with batch queries."""
    # Platform-wide stats using aggregations
    platform_stats = {
        'total_users': User.objects.count(),
        'total_shops': Shop.objects.count(),
        'total_listings': Listing.objects.count(),
        'active_listings': Listing.objects.filter(status='active').count(),
        'total_transactions': Transaction.objects.count(),
    }
    
    # Revenue stats in one query
    revenue = Transaction.objects.aggregate(
        total_revenue=Sum('amount'),
        week_revenue=Sum('amount', filter=Q(created_at__gte=timezone.now()-timedelta(days=7))),
        month_revenue=Sum('amount', filter=Q(created_at__gte=timezone.now()-timedelta(days=30))),
    )
    
    # Recent activity using optimized queries
    recent_users = get_optimized_users_queryset().order_by('-date_joined')[:5]
    recent_shops = get_optimized_shops_queryset().order_by('-created_at')[:5]
    recent_listings = get_optimized_listings_queryset().order_by('-created_at')[:5]
    
    # Top sellers
    top_sellers = Shop.objects.select_related('owner').annotate(
        revenue=Sum('listing__transaction__amount')
    ).order_by('-revenue')[:10]
    
    return {
        'platform': platform_stats,
        'revenue': revenue,
        'recent_users': recent_users,
        'recent_shops': recent_shops,
        'recent_listings': recent_listings,
        'top_sellers': top_sellers,
    }


def get_moderation_queue_optimized(status='pending'):
    """Get moderation queue with all needed data in minimal queries."""
    return Listing.objects.filter(
        status=status
    ).select_related(
        'shop', 'shop__owner', 'category'
    ).prefetch_related(
        Prefetch(
            'adminauditlog_set',
            queryset=AdminAuditLog.objects.select_related('admin_user').order_by('-created_at')[:3]
        )
    ).annotate(
        flag_count=Count('adminauditlog', filter=Q(adminauditlog__action='flag')),
        days_pending=timezone.now() - timezone.F('created_at')
    ).order_by('created_at')


def get_audit_logs_with_details(limit=100, filters=None):
    """Get audit logs with all related details."""
    logs = AdminAuditLog.objects.select_related('admin_user').only(
        'id', 'admin_user_id', 'admin_username', 'action', 'content_type',
        'object_id', 'object_str', 'status', 'reason', 'created_at'
    )
    
    if filters:
        if 'action' in filters:
            logs = logs.filter(action=filters['action'])
        if 'admin_id' in filters:
            logs = logs.filter(admin_user_id=filters['admin_id'])
        if 'content_type' in filters:
            logs = logs.filter(content_type=filters['content_type'])
        if 'status' in filters:
            logs = logs.filter(status=filters['status'])
        if 'date_from' in filters:
            logs = logs.filter(created_at__gte=filters['date_from'])
        if 'date_to' in filters:
            logs = logs.filter(created_at__lte=filters['date_to'])
    
    return logs.order_by('-created_at')[:limit]


def get_analytics_data_optimized(days=30):
    """Get all analytics data with minimal database queries."""
    start_date = timezone.now() - timedelta(days=days)
    
    # Growth metrics
    new_users_by_day = User.objects.filter(
        date_joined__gte=start_date
    ).extra(
        select={'day': 'DATE(date_joined)'}
    ).values('day').annotate(count=Count('id')).order_by('day')
    
    new_shops_by_day = Shop.objects.filter(
        created_at__gte=start_date
    ).extra(
        select={'day': 'DATE(created_at)'}
    ).values('day').annotate(count=Count('id')).order_by('day')
    
    # Revenue by category
    revenue_by_category = Transaction.objects.filter(
        created_at__gte=start_date
    ).values('listing__category__name').annotate(
        revenue=Sum('amount'),
        count=Count('id')
    ).order_by('-revenue')
    
    # Category performance
    category_performance = Category.objects.annotate(
        listing_count=Count('listing'),
        active_count=Count('listing', filter=Q(listing__status='active')),
        revenue=Sum('listing__transaction__amount')
    ).order_by('-revenue')[:20]
    
    return {
        'new_users_by_day': list(new_users_by_day),
        'new_shops_by_day': list(new_shops_by_day),
        'revenue_by_category': list(revenue_by_category),
        'category_performance': category_performance,
    }


# ============================================================
# QUERY COUNT ANALYSIS (for debugging)
# ============================================================

def print_query_stats(func_name, queryset=None, count=None):
    """Print query statistics for debugging (development only)."""
    from django.db import connection, reset_queries
    from django.conf import settings
    
    if not settings.DEBUG:
        return
    
    if queryset:
        list(queryset)  # Force evaluation
    
    query_count = len(connection.queries)
    total_time = sum(float(q['time']) for q in connection.queries) if connection.queries else 0
    
    print(f"\n[QUERY STATS] {func_name}")
    print(f"  Queries: {query_count}")
    print(f"  Time: {total_time:.2f}s")
    
    if count:
        print(f"  Per item: {query_count/count:.2f} queries")


def analyze_queryset_queries(queryset_or_result):
    """
    Analyze number of queries executed.
    Use in development to catch N+1 problems.
    """
    from django.db import connection
    from django.conf import settings
    
    if settings.DEBUG:
        # Force evaluation if queryset
        if hasattr(queryset_or_result, '_fetch_all'):
            list(queryset_or_result)
        
        num_queries = len(connection.queries)
        total_time = sum(float(q['time']) for q in connection.queries)
        
        return {
            'query_count': num_queries,
            'total_time': total_time,
            'avg_time': total_time / num_queries if num_queries > 0 else 0,
            'queries': connection.queries if settings.DEBUG else []
        }
    
    return {'error': 'Query analysis only available in DEBUG mode'}
