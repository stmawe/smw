"""
Admin REST API Endpoints
RESTful API for programmatic admin operations and frontend integrations.
All endpoints require proper authentication and permission checks.
"""

from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta
import json

from .models import (
    User, Category, Theme,
    AdminAuditLog, AdminActivityFeed
)
from mydak.models import Shop, Listing, Transaction
from .admin_permissions import permission_required, AdminPermission


# ============================================================
# USER MANAGEMENT API
# ============================================================

@login_required
@permission_required(AdminPermission.VIEW_USERS)
@require_http_methods(["GET"])
def api_users_list(request):
    """
    GET /admin/api/users/
    List all users with filtering, search, and pagination.
    """
    # Pagination
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 50))
    per_page = min(per_page, 100)  # Max 100 per page
    
    # Filtering
    search = request.GET.get('search', '')
    role = request.GET.get('role', '')
    is_staff = request.GET.get('is_staff', '')
    
    users = User.objects.all()
    
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    if role:
        users = users.filter(role=role)
    
    if is_staff == 'true':
        users = users.filter(is_staff=True)
    elif is_staff == 'false':
        users = users.filter(is_staff=False)
    
    total = users.count()
    start = (page - 1) * per_page
    end = start + per_page
    
    users_page = users[start:end]
    
    data = {
        'count': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page,
        'results': [
            {
                'id': u.id,
                'username': u.username,
                'email': u.email,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'is_staff': u.is_staff,
                'is_active': u.is_active,
                'role': u.role,
                'date_joined': u.date_joined.isoformat(),
            }
            for u in users_page
        ]
    }
    
    return JsonResponse(data)


@login_required
@permission_required(AdminPermission.MANAGE_USERS)
@require_http_methods(["POST"])
def api_user_update(request, user_id):
    """
    POST /admin/api/users/<id>/
    Update a user via API.
    """
    user = get_object_or_404(User, id=user_id)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    # Update allowed fields
    if 'email' in data:
        user.email = data['email']
    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    if 'is_staff' in data:
        user.is_staff = data['is_staff']
    if 'is_active' in data:
        user.is_active = data['is_active']
    if 'role' in data:
        user.role = data['role']
    
    user.save()
    
    response_data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_staff': user.is_staff,
        'is_active': user.is_active,
        'role': user.role,
        'updated_at': timezone.now().isoformat(),
    }
    
    return JsonResponse(response_data)


# ============================================================
# SHOP MANAGEMENT API
# ============================================================

@login_required
@permission_required(AdminPermission.VIEW_SHOPS)
@require_http_methods(["GET"])
def api_shops_list(request):
    """
    GET /admin/api/shops/
    List all shops with stats.
    """
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 50))
    per_page = min(per_page, 100)
    
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    
    shops = Shop.objects.annotate(listing_count=Count('listing'))
    
    if search:
        shops = shops.filter(Q(name__icontains=search))
    
    if status == 'active':
        shops = shops.filter(is_active=True)
    elif status == 'inactive':
        shops = shops.filter(is_active=False)
    
    total = shops.count()
    start = (page - 1) * per_page
    end = start + per_page
    
    shops_page = shops[start:end]
    
    data = {
        'count': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page,
        'results': [
            {
                'id': s.id,
                'name': s.name,
                'owner_id': s.owner.id if hasattr(s, 'owner') else None,
                'owner_email': s.owner.email if hasattr(s, 'owner') else None,
                'is_active': s.is_active,
                'listing_count': s.listing_count,
                'created_at': s.created_at.isoformat() if hasattr(s, 'created_at') else None,
            }
            for s in shops_page
        ]
    }
    
    return JsonResponse(data)


# ============================================================
# LISTING MANAGEMENT API
# ============================================================

@login_required
@permission_required(AdminPermission.VIEW_LISTINGS)
@require_http_methods(["GET"])
def api_listings_list(request):
    """
    GET /admin/api/listings/
    List listings with filtering and moderation status.
    """
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 50))
    per_page = min(per_page, 100)
    
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    
    listings = Listing.objects.all()
    
    if search:
        listings = listings.filter(Q(title__icontains=search))
    
    if status:
        listings = listings.filter(status=status)
    
    total = listings.count()
    start = (page - 1) * per_page
    end = start + per_page
    
    listings_page = listings[start:end]
    
    data = {
        'count': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page,
        'results': [
            {
                'id': l.id,
                'title': l.title if hasattr(l, 'title') else '',
                'status': l.status if hasattr(l, 'status') else 'active',
                'is_featured': l.is_featured if hasattr(l, 'is_featured') else False,
                'shop_id': l.shop.id if hasattr(l, 'shop') else None,
                'created_at': l.created_at.isoformat() if hasattr(l, 'created_at') else None,
            }
            for l in listings_page
        ]
    }
    
    return JsonResponse(data)


@login_required
@permission_required(AdminPermission.MANAGE_LISTINGS)
@require_http_methods(["POST"])
def api_listing_action(request, listing_id):
    """
    POST /admin/api/listings/<id>/action/
    Perform actions on a listing (approve, reject, feature, etc.)
    """
    listing = get_object_or_404(Listing, id=listing_id)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    action = data.get('action', '')
    reason = data.get('reason', '')
    
    if action == 'approve':
        listing.status = 'active'
    elif action == 'reject':
        listing.status = 'rejected'
    elif action == 'feature':
        if hasattr(listing, 'is_featured'):
            listing.is_featured = True
    elif action == 'unfeature':
        if hasattr(listing, 'is_featured'):
            listing.is_featured = False
    else:
        return JsonResponse({'error': 'Invalid action'}, status=400)
    
    listing.save()
    
    response_data = {
        'id': listing.id,
        'title': listing.title if hasattr(listing, 'title') else '',
        'status': listing.status if hasattr(listing, 'status') else 'active',
        'action': action,
        'updated_at': timezone.now().isoformat(),
    }
    
    return JsonResponse(response_data)


# ============================================================
# TRANSACTION MANAGEMENT API
# ============================================================

@login_required
@permission_required(AdminPermission.VIEW_TRANSACTIONS)
@require_http_methods(["GET"])
def api_transactions_list(request):
    """
    GET /admin/api/transactions/
    List transactions with filtering.
    """
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 50))
    per_page = min(per_page, 100)
    
    status = request.GET.get('status', '')
    
    transactions = Transaction.objects.select_related('seller', 'buyer').all()
    
    if status:
        transactions = transactions.filter(status=status)
    
    total = transactions.count()
    start = (page - 1) * per_page
    end = start + per_page
    
    transactions_page = transactions[start:end]
    
    data = {
        'count': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page,
        'results': [
            {
                'id': t.id,
                'transaction_id': t.transaction_id if hasattr(t, 'transaction_id') else str(t.id),
                'seller_id': t.seller.id if hasattr(t, 'seller') and t.seller else None,
                'buyer_id': t.buyer.id if hasattr(t, 'buyer') and t.buyer else None,
                'amount': float(t.amount) if hasattr(t, 'amount') else 0,
                'status': t.status if hasattr(t, 'status') else 'completed',
                'created_at': t.created_at.isoformat() if hasattr(t, 'created_at') else None,
            }
            for t in transactions_page
        ]
    }
    
    return JsonResponse(data)


@login_required
@permission_required(AdminPermission.REFUND_TRANSACTIONS)
@require_http_methods(["POST"])
def api_transaction_refund(request, transaction_id):
    """
    POST /admin/api/transactions/<id>/refund/
    Process a refund for a transaction.
    """
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    reason = data.get('reason', 'Admin refund')
    
    transaction.status = 'refunded'
    transaction.save()
    
    response_data = {
        'id': transaction.id,
        'status': 'refunded',
        'reason': reason,
        'updated_at': timezone.now().isoformat(),
    }
    
    return JsonResponse(response_data)


# ============================================================
# AUDIT LOGS API
# ============================================================

@login_required
@permission_required(AdminPermission.VIEW_AUDIT_LOGS)
@require_http_methods(["GET"])
def api_audit_logs_list(request):
    """
    GET /admin/api/audit-logs/
    List audit logs with filtering.
    """
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 50))
    per_page = min(per_page, 100)
    
    action = request.GET.get('action', '')
    admin_id = request.GET.get('admin_id', '')
    content_type = request.GET.get('content_type', '')
    
    logs = AdminAuditLog.objects.select_related('admin_user').all()
    
    if action:
        logs = logs.filter(action=action)
    if admin_id:
        logs = logs.filter(admin_user_id=admin_id)
    if content_type:
        logs = logs.filter(content_type=content_type)
    
    logs = logs.order_by('-created_at')
    
    total = logs.count()
    start = (page - 1) * per_page
    end = start + per_page
    
    logs_page = logs[start:end]
    
    data = {
        'count': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page,
        'results': [
            {
                'id': log.id,
                'admin': log.admin_username,
                'action': log.action,
                'content_type': log.content_type,
                'object_id': log.object_id,
                'object_str': log.object_str,
                'status': log.status,
                'created_at': log.created_at.isoformat(),
            }
            for log in logs_page
        ]
    }
    
    return JsonResponse(data)


@login_required
@permission_required(AdminPermission.VIEW_AUDIT_LOGS)
@require_http_methods(["GET"])
def api_audit_log_detail(request, log_id):
    """
    GET /admin/api/audit-logs/<id>/
    Get detailed audit log entry.
    """
    log = get_object_or_404(AdminAuditLog, id=log_id)
    
    data = {
        'id': log.id,
        'admin': log.admin_username,
        'action': log.action,
        'content_type': log.content_type,
        'object_id': log.object_id,
        'object_str': log.object_str,
        'changes': log.changes,
        'old_values': log.old_values,
        'new_values': log.new_values,
        'reason': log.reason,
        'ip_address': log.ip_address,
        'status': log.status,
        'error_message': log.error_message,
        'created_at': log.created_at.isoformat(),
    }
    
    return JsonResponse(data)


# ============================================================
# ANALYTICS API
# ============================================================

@login_required
@permission_required(AdminPermission.VIEW_ANALYTICS)
@require_http_methods(["GET"])
def api_analytics_summary(request):
    """
    GET /admin/api/analytics/summary/
    Get summary analytics for dashboard.
    """
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # User metrics
    total_users = User.objects.count()
    new_users = User.objects.filter(date_joined__gte=start_date).count()
    
    # Shop metrics
    total_shops = Shop.objects.count()
    active_shops = Shop.objects.filter(is_active=True).count()
    
    # Listing metrics
    total_listings = Listing.objects.count()
    active_listings = Listing.objects.filter(is_active=True).count()
    new_listings = Listing.objects.filter(created_at__gte=start_date).count()
    
    # Transaction metrics
    total_transactions = Transaction.objects.count()
    transactions_period = Transaction.objects.filter(created_at__gte=start_date)
    revenue_period = transactions_period.aggregate(Sum('amount'))['amount__sum'] or 0
    
    data = {
        'period_days': days,
        'users': {
            'total': total_users,
            'new': new_users,
        },
        'shops': {
            'total': total_shops,
            'active': active_shops,
        },
        'listings': {
            'total': total_listings,
            'active': active_listings,
            'new': new_listings,
        },
        'transactions': {
            'total': total_transactions,
            'period': transactions_period.count(),
            'revenue_period': float(revenue_period),
        },
        'timestamp': timezone.now().isoformat(),
    }
    
    return JsonResponse(data)


@login_required
@permission_required(AdminPermission.VIEW_ANALYTICS)
@require_http_methods(["GET"])
def api_analytics_top_sellers(request):
    """
    GET /admin/api/analytics/top-sellers/
    Get top sellers by transaction count or revenue.
    """
    days = int(request.GET.get('days', 30))
    sort_by = request.GET.get('sort_by', 'count')  # count or revenue
    limit = min(int(request.GET.get('limit', 10)), 50)
    
    start_date = timezone.now() - timedelta(days=days)
    
    transactions = Transaction.objects.filter(created_at__gte=start_date)
    
    if sort_by == 'revenue':
        sellers = transactions.values('seller').annotate(
            total_revenue=Sum('amount'),
            transaction_count=Count('*')
        ).order_by('-total_revenue')[:limit]
    else:
        sellers = transactions.values('seller').annotate(
            transaction_count=Count('*'),
            total_revenue=Sum('amount')
        ).order_by('-transaction_count')[:limit]
    
    # Enrich with seller info
    results = []
    for seller_data in sellers:
        seller = User.objects.filter(id=seller_data['seller']).first()
        if seller:
            results.append({
                'seller_id': seller.id,
                'seller_name': seller.username,
                'seller_email': seller.email,
                'transaction_count': seller_data['transaction_count'],
                'total_revenue': float(seller_data['total_revenue'] or 0),
            })
    
    data = {
        'period_days': days,
        'sort_by': sort_by,
        'count': len(results),
        'results': results,
    }
    
    return JsonResponse(data)


# ============================================================
# PERMISSIONS API
# ============================================================

@login_required
@permission_required(AdminPermission.MANAGE_ADMINS)
@require_http_methods(["GET"])
def api_user_permissions(request, user_id):
    """
    GET /admin/api/users/<id>/permissions/
    Get all permissions for a user.
    """
    user = get_object_or_404(User, id=user_id)
    
    # Get permissions based on is_staff/is_superuser
    from .admin_permissions import AdminPermissions
    perms = AdminPermissions(user)
    
    data = {
        'user_id': user.id,
        'username': user.username,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'admin_role': str(perms.role.value) if perms.role else None,
        'permissions': list(perms.get_all_permissions()),
        'has_manage_users': perms.has(AdminPermission.MANAGE_USERS),
        'has_manage_shops': perms.has(AdminPermission.MANAGE_SHOPS),
        'has_manage_listings': perms.has(AdminPermission.MANAGE_LISTINGS),
        'has_moderate_content': perms.has(AdminPermission.MODERATE_CONTENT),
        'has_manage_transactions': perms.has(AdminPermission.MANAGE_TRANSACTIONS),
        'has_manage_settings': perms.has(AdminPermission.MANAGE_SETTINGS),
        'has_view_audit_logs': perms.has(AdminPermission.VIEW_AUDIT_LOGS),
    }
    
    return JsonResponse(data)


# ============================================================
# ACTIVITY FEED API
# ============================================================

@login_required
@permission_required(AdminPermission.VIEW_AUDIT_LOGS)
@require_http_methods(["GET"])
def api_activity_feed(request):
    """
    GET /admin/api/activity-feed/
    Get recent activity feed for dashboard.
    """
    limit = min(int(request.GET.get('limit', 50)), 100)
    
    activities = AdminActivityFeed.objects.filter(
        is_visible=True
    ).select_related('admin_user').order_by('-created_at')[:limit]
    
    data = {
        'count': len(activities),
        'results': [
            {
                'id': a.id,
                'admin': a.admin_user.username if a.admin_user else 'System',
                'type': a.activity_type,
                'description': a.description,
                'severity': a.severity,
                'icon': a.icon,
                'link_url': a.link_url,
                'created_at': a.created_at.isoformat(),
            }
            for a in activities
        ]
    }
    
    return JsonResponse(data)
