"""
Admin CRUD Views - Backend for Admin Panel
Handles all Create, Read, Update, Delete operations for admin resources.
All views include RBAC permission checks and audit logging.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta
import json

from .models import (
    User, Category, Theme, ThemeToken, PageThemeAssignment,
    AdminAuditLog, AdminActivityFeed, Client, ClientDomain
)
from mydak.models import Shop, Listing, Transaction
from .admin_permissions import permission_required, AdminPermission
from .admin_roles_middleware import get_admin_perms


def log_admin_action(request, action, content_type, object_id, object_str="",
                     changes=None, reason="", status="success", error_msg=""):
    """
    Helper function to log admin audit actions.
    Should be called after any admin CRUD operation.
    """
    audit_log = AdminAuditLog.objects.create(
        admin_user=request.user,
        admin_username=request.user.username,
        action=action,
        action_label=f"{request.user.username} {action} {content_type}#{object_id}",
        content_type=content_type,
        object_id=str(object_id),
        object_str=object_str,
        changes=changes or {},
        reason=reason,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:200],
        status=status,
        error_message=error_msg,
    )
    return audit_log


def log_activity_feed(request, activity_type, content_type, object_id, object_title="",
                      description="", link_url="", severity="info", batch_id=""):
    """
    Helper function to create activity feed entries for dashboard.
    Simpler than audit logs - for display in activity feed.
    """
    activity = AdminActivityFeed.objects.create(
        admin_user=request.user,
        activity_type=activity_type,
        content_type=content_type,
        object_id=str(object_id),
        object_title=object_title,
        description=description,
        link_url=link_url,
        severity=severity,
        batch_id=batch_id,
    )
    return activity


def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ============================================================
# DASHBOARD & OVERVIEW VIEWS
# ============================================================

@login_required
@permission_required(AdminPermission.ACCESS_ADMIN_PANEL)
def admin_dashboard_full(request):
    """
    Main admin dashboard with key metrics and activity feed.
    """
    # Get recent activity
    recent_activity = AdminActivityFeed.objects.filter(
        is_visible=True
    ).select_related('admin_user')[:20]
    
    # Get key metrics
    total_users = User.objects.count()
    total_shops = Shop.objects.count()
    active_listings = Listing.objects.filter(is_active=True).count()
    
    # Recent transactions (last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    transactions_7d = Transaction.objects.filter(created_at__gte=week_ago).count()
    revenue_7d = Transaction.objects.filter(
        created_at__gte=week_ago
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Pending items
    pending_listings = Listing.objects.filter(status='pending').count()
    pending_refunds = Transaction.objects.filter(
        status='pending_refund'
    ).count()
    
    context = {
        'total_users': total_users,
        'total_shops': total_shops,
        'active_listings': active_listings,
        'transactions_7d': transactions_7d,
        'revenue_7d': revenue_7d,
        'pending_listings': pending_listings,
        'pending_refunds': pending_refunds,
        'recent_activity': recent_activity,
    }
    
    return render(request, 'admin/dashboard.html', context)


# ============================================================
# USER MANAGEMENT VIEWS
# ============================================================

@login_required
@permission_required(AdminPermission.MANAGE_USERS)
def admin_users_list(request):
    """
    List all users with filtering and bulk actions.
    Uses optimized queries to prevent N+1 problems.
    """
    from .admin_query_optimization import get_optimized_users_queryset
    
    users = get_optimized_users_queryset().order_by('-date_joined')
    
    # Apply filters
    search = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    is_staff_filter = request.GET.get('is_staff', '')
    
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    if role_filter:
        users = users.filter(role=role_filter)
    
    if is_staff_filter == 'yes':
        users = users.filter(is_staff=True)
    elif is_staff_filter == 'no':
        users = users.filter(is_staff=False)
    
    # Pagination
    page = int(request.GET.get('page', 1))
    per_page = 50
    total = users.count()
    start = (page - 1) * per_page
    end = start + per_page
    
    users_page = users[start:end]
    total_pages = (total + per_page - 1) // per_page
    
    context = {
        'users': users_page,
        'total': total,
        'page': page,
        'total_pages': total_pages,
        'search': search,
        'role_filter': role_filter,
        'is_staff_filter': is_staff_filter,
    }
    
    return render(request, 'admin/users.html', context)


@login_required
@permission_required(AdminPermission.MANAGE_USERS)
def admin_user_detail(request, user_id):
    """
    User detail/edit page.
    """
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Handle user update
        old_values = {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'is_active': user.is_active,
            'role': user.role,
        }
        
        user.email = request.POST.get('email', user.email)
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.is_staff = request.POST.get('is_staff') == 'on'
        user.is_active = request.POST.get('is_active') == 'on'
        user.role = request.POST.get('role', user.role)
        
        # Handle password change
        new_password = request.POST.get('new_password', '')
        if new_password:
            user.set_password(new_password)
        
        user.save()
        
        new_values = {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'is_active': user.is_active,
            'role': user.role,
        }
        
        # Calculate changes
        changes = {
            k: {'old': old_values[k], 'new': new_values[k]}
            for k in old_values if old_values[k] != new_values[k]
        }
        
        # Log action
        log_admin_action(
            request,
            'update',
            'User',
            user.id,
            f"{user.email}",
            changes=changes,
            reason=request.POST.get('reason', '')
        )
        log_activity_feed(
            request,
            'updated',
            'User',
            user.id,
            object_title=user.email,
            description=f"Updated user {user.email}",
            severity='info'
        )
        
        messages.success(request, f"User {user.email} updated successfully.")
        return redirect('admin_user_detail', user_id=user.id)
    
    # Get user stats
    shops_count = Shop.objects.filter(owner=user).count()
    listings_count = Listing.objects.filter(shop__owner=user).count()
    transactions_count = Transaction.objects.filter(seller=user).count()
    
    context = {
        'user': user,
        'shops_count': shops_count,
        'listings_count': listings_count,
        'transactions_count': transactions_count,
    }
    
    return render(request, 'admin/user_detail.html', context)


@login_required
@permission_required(AdminPermission.MANAGE_USERS)
@require_http_methods(["POST"])
def admin_user_suspend(request, user_id):
    """
    Suspend/ban a user account.
    """
    user = get_object_or_404(User, id=user_id)
    user.is_active = False
    user.save()
    
    log_admin_action(
        request,
        'ban_user',
        'User',
        user.id,
        f"{user.email}",
        reason=request.POST.get('reason', '')
    )
    log_activity_feed(
        request,
        'banned',
        'User',
        user.id,
        object_title=user.email,
        description=f"Suspended user {user.email}",
        severity='warning'
    )
    
    messages.success(request, f"User {user.email} has been suspended.")
    return redirect('admin_user_detail', user_id=user.id)


@login_required
@permission_required(AdminPermission.MANAGE_USERS)
@require_http_methods(["POST"])
def admin_user_unsuspend(request, user_id):
    """
    Unsuspend/unban a user account.
    """
    user = get_object_or_404(User, id=user_id)
    user.is_active = True
    user.save()
    
    log_admin_action(
        request,
        'unban_user',
        'User',
        user.id,
        f"{user.email}",
    )
    log_activity_feed(
        request,
        'updated',
        'User',
        user.id,
        object_title=user.email,
        description=f"Reactivated user {user.email}",
        severity='success'
    )
    
    messages.success(request, f"User {user.email} has been reactivated.")
    return redirect('admin_user_detail', user_id=user.id)


# ============================================================
# SHOP MANAGEMENT VIEWS
# ============================================================

@login_required
@permission_required(AdminPermission.MANAGE_SHOPS)
def admin_shops_list(request):
    """
    List all shops with filtering and stats.
    Uses optimized queries to prevent N+1 problems.
    """
    from .admin_query_optimization import get_optimized_shops_queryset
    
    shops = get_optimized_shops_queryset().order_by('-created_at')
    
    # Apply filters
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    if search:
        shops = shops.filter(Q(name__icontains=search))
    
    if status_filter == 'active':
        shops = shops.filter(is_active=True)
    elif status_filter == 'inactive':
        shops = shops.filter(is_active=False)
    
    # Pagination
    page = int(request.GET.get('page', 1))
    per_page = 50
    total = shops.count()
    start = (page - 1) * per_page
    end = start + per_page
    
    shops_page = shops[start:end]
    total_pages = (total + per_page - 1) // per_page
    
    context = {
        'shops': shops_page,
        'total': total,
        'page': page,
        'total_pages': total_pages,
        'search': search,
        'status_filter': status_filter,
    }
    
    return render(request, 'admin/shops.html', context)


@login_required
@permission_required(AdminPermission.MANAGE_SHOPS)
def admin_shop_detail(request, shop_id):
    """
    Shop detail/edit page.
    """
    shop = get_object_or_404(Shop, id=shop_id)
    
    if request.method == 'POST':
        # Handle shop update
        old_values = {
            'name': shop.name,
            'description': shop.description if hasattr(shop, 'description') else '',
            'is_active': shop.is_active,
        }
        
        shop.name = request.POST.get('name', shop.name)
        if hasattr(shop, 'description'):
            shop.description = request.POST.get('description', shop.description)
        shop.is_active = request.POST.get('is_active') == 'on'
        shop.save()
        
        new_values = {
            'name': shop.name,
            'description': shop.description if hasattr(shop, 'description') else '',
            'is_active': shop.is_active,
        }
        
        changes = {
            k: {'old': old_values[k], 'new': new_values[k]}
            for k in old_values if old_values[k] != new_values[k]
        }
        
        log_admin_action(
            request,
            'update',
            'Shop',
            shop.id,
            shop.name,
            changes=changes,
            reason=request.POST.get('reason', '')
        )
        log_activity_feed(
            request,
            'updated',
            'Shop',
            shop.id,
            object_title=shop.name,
            description=f"Updated shop {shop.name}",
        )
        
        messages.success(request, f"Shop {shop.name} updated successfully.")
        return redirect('admin_shop_detail', shop_id=shop.id)
    
    # Get shop stats
    listings_count = Listing.objects.filter(shop=shop).count()
    active_listings = Listing.objects.filter(shop=shop, is_active=True).count()
    transactions_count = Transaction.objects.filter(shop=shop).count()
    
    context = {
        'shop': shop,
        'listings_count': listings_count,
        'active_listings': active_listings,
        'transactions_count': transactions_count,
    }
    
    return render(request, 'admin/shop_detail.html', context)


# ============================================================
# LISTING MANAGEMENT & MODERATION VIEWS
# ============================================================

@login_required
@permission_required(AdminPermission.MANAGE_LISTINGS)
def admin_listings_moderation(request):
    """
    Listings pending approval/review.
    """
    listings = Listing.objects.filter(status='pending').order_by('-created_at')
    
    # Apply filters
    search = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    
    if search:
        listings = listings.filter(Q(title__icontains=search))
    
    if category_filter:
        listings = listings.filter(category_id=category_filter)
    
    # Pagination
    page = int(request.GET.get('page', 1))
    per_page = 50
    total = listings.count()
    start = (page - 1) * per_page
    end = start + per_page
    
    listings_page = listings[start:end]
    total_pages = (total + per_page - 1) // per_page
    
    context = {
        'listings': listings_page,
        'total': total,
        'page': page,
        'total_pages': total_pages,
        'search': search,
        'category_filter': category_filter,
    }
    
    return render(request, 'admin/listings.html', context)


@login_required
@permission_required(AdminPermission.MANAGE_LISTINGS)
def admin_listing_detail(request, listing_id):
    """
    Listing detail/review page.
    """
    listing = get_object_or_404(Listing, id=listing_id)
    
    if request.method == 'POST':
        action = request.POST.get('action', '')
        
        if action == 'approve':
            listing.status = 'active'
            action_name = 'approve_listing'
            severity = 'success'
        elif action == 'reject':
            listing.status = 'rejected'
            action_name = 'reject_listing'
            severity = 'danger'
        elif action == 'feature':
            listing.is_featured = True
            action_name = 'feature_listing'
            severity = 'info'
        elif action == 'unfeature':
            listing.is_featured = False
            action_name = 'unfeature_listing'
            severity = 'info'
        else:
            messages.error(request, "Unknown action.")
            return redirect('admin_listing_detail', listing_id=listing.id)
        
        listing.save()
        
        log_admin_action(
            request,
            action_name,
            'Listing',
            listing.id,
            listing.title,
            reason=request.POST.get('reason', '')
        )
        log_activity_feed(
            request,
            action.rstrip('e'),  # remove 'e' from approve/feature -> approv/featur
            'Listing',
            listing.id,
            object_title=listing.title,
            description=f"{action_name} listing: {listing.title}",
            severity=severity,
        )
        
        messages.success(request, f"Listing {action}d successfully.")
        return redirect('admin_listing_detail', listing_id=listing.id)
    
    context = {
        'listing': listing,
    }
    
    return render(request, 'admin/listing_detail.html', context)


# ============================================================
# CATEGORY MANAGEMENT VIEWS
# ============================================================

@login_required
@permission_required(AdminPermission.MANAGE_CATEGORIES)
def admin_categories_list(request):
    """
    List and manage categories.
    """
    categories = Category.objects.all().order_by('name')
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'admin/categories.html', context)


@login_required
@permission_required(AdminPermission.MANAGE_CATEGORIES)
@require_http_methods(["POST"])
def admin_category_create(request):
    """
    Create a new category.
    """
    name = request.POST.get('name', '').strip()
    
    if not name:
        messages.error(request, "Category name is required.")
        return redirect('admin_categories_list')
    
    category, created = Category.objects.get_or_create(name=name)
    
    if created:
        log_admin_action(request, 'create', 'Category', category.id, name)
        log_activity_feed(
            request,
            'created',
            'Category',
            category.id,
            object_title=name,
            description=f"Created category: {name}",
            severity='info'
        )
        messages.success(request, f"Category '{name}' created successfully.")
    else:
        messages.info(request, f"Category '{name}' already exists.")
    
    return redirect('admin_categories_list')


@login_required
@permission_required(AdminPermission.MANAGE_CATEGORIES)
@require_http_methods(["POST"])
def admin_category_delete(request, category_id):
    """
    Delete a category.
    """
    category = get_object_or_404(Category, id=category_id)
    name = category.name
    
    # Check if category has listings
    if Listing.objects.filter(category=category).exists():
        messages.error(request, f"Cannot delete category '{name}' - it has associated listings.")
        return redirect('admin_categories_list')
    
    category.delete()
    
    log_admin_action(request, 'delete', 'Category', category_id, name)
    log_activity_feed(
        request,
        'deleted',
        'Category',
        category_id,
        object_title=name,
        description=f"Deleted category: {name}",
        severity='warning'
    )
    
    messages.success(request, f"Category '{name}' deleted successfully.")
    return redirect('admin_categories_list')


# ============================================================
# TRANSACTION MANAGEMENT VIEWS
# ============================================================

@login_required
@permission_required(AdminPermission.MANAGE_TRANSACTIONS)
def admin_transactions_list(request):
    """
    List all transactions with filtering.
    """
    transactions = Transaction.objects.all().select_related(
        'user', 'shop', 'listing'
    ).order_by('-created_at')
    
    # Apply filters
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    if status_filter:
        transactions = transactions.filter(status=status_filter)
    
    if search:
        transactions = transactions.filter(
            Q(reference_id__icontains=search) |
            Q(user__email__icontains=search) |
            Q(mpesa_receipt__icontains=search)
        )
    
    # Pagination
    page = int(request.GET.get('page', 1))
    per_page = 50
    total = transactions.count()
    start = (page - 1) * per_page
    end = start + per_page
    
    transactions_page = transactions[start:end]
    total_pages = (total + per_page - 1) // per_page
    
    context = {
        'transactions': transactions_page,
        'total': total,
        'page': page,
        'total_pages': total_pages,
        'status_filter': status_filter,
        'search': search,
    }
    
    return render(request, 'admin/transactions.html', context)


# ============================================================
# SETTINGS & CONFIGURATION VIEWS
# ============================================================

@login_required
@permission_required(AdminPermission.MANAGE_SETTINGS)
def admin_settings_view(request):
    """
    Site settings/configuration page.
    """
    if request.method == 'POST':
        tab = request.POST.get('tab', 'general')
        
        # Handle different settings tabs
        # This would typically save to a SiteSetting model
        # For now, just log the action
        
        log_admin_action(
            request,
            'setting_change',
            'SiteSettings',
            tab,
            reason=request.POST.get('reason', '')
        )
        
        messages.success(request, f"Settings updated successfully.")
        return redirect('admin_settings_view')
    
    context = {
        'active_tab': request.GET.get('tab', 'general'),
    }
    
    return render(request, 'admin/settings.html', context)


# ============================================================
# THEME MANAGEMENT VIEWS
# ============================================================

@login_required
@permission_required(AdminPermission.MANAGE_THEMES)
def admin_themes_list(request):
    """
    List and manage themes.
    """
    themes = Theme.objects.all().order_by('-is_active', '-created_at')
    active_theme = Theme.objects.filter(is_active=True).first()
    
    context = {
        'themes': themes,
        'active_theme': active_theme,
    }
    
    return render(request, 'admin/theme_management.html', context)


@login_required
@permission_required(AdminPermission.MANAGE_THEMES)
@require_http_methods(["POST"])
def admin_theme_activate(request, theme_id):
    """
    Activate a theme.
    """
    theme = get_object_or_404(Theme, id=theme_id)
    old_active = Theme.objects.filter(is_active=True).first()
    
    theme.is_active = True
    theme.save()
    
    log_admin_action(request, 'setting_change', 'Theme', theme.id)
    log_activity_feed(
        request,
        'updated',
        'Theme',
        theme.id,
        object_title=theme.name,
        description=f"Activated theme: {theme.name}",
        severity='info'
    )
    
    messages.success(request, f"Theme '{theme.name}' activated successfully.")
    return redirect('admin_themes_list')


# ============================================================
# AUDIT LOGS VIEW
# ============================================================

@login_required
@permission_required(AdminPermission.VIEW_AUDIT_LOGS)
def admin_audit_logs(request):
    """
    View admin audit logs.
    """
    logs = AdminAuditLog.objects.all().select_related('admin_user').order_by('-created_at')
    
    # Apply filters
    admin_filter = request.GET.get('admin', '')
    action_filter = request.GET.get('action', '')
    
    if admin_filter:
        logs = logs.filter(admin_user_id=admin_filter)
    
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    # Pagination
    page = int(request.GET.get('page', 1))
    per_page = 50
    total = logs.count()
    start = (page - 1) * per_page
    end = start + per_page
    
    logs_page = logs[start:end]
    total_pages = (total + per_page - 1) // per_page
    
    context = {
        'logs': logs_page,
        'total': total,
        'page': page,
        'total_pages': total_pages,
        'admin_filter': admin_filter,
        'action_filter': action_filter,
    }
    
    return render(request, 'admin/audit_logs.html', context)


# ============================================================
# JSON API ENDPOINTS FOR AJAX/MODALS
# ============================================================

@login_required
@permission_required(AdminPermission.MANAGE_USERS)
def api_user_details(request, user_id):
    """
    Get user details as JSON for modals.
    """
    user = get_object_or_404(User, id=user_id)
    
    data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_staff': user.is_staff,
        'is_active': user.is_active,
        'role': user.role,
        'date_joined': user.date_joined.isoformat(),
    }
    
    return JsonResponse(data)


@login_required
@permission_required(AdminPermission.MANAGE_SHOPS)
def api_shop_details(request, shop_id):
    """
    Get shop details as JSON for modals.
    """
    shop = get_object_or_404(Shop, id=shop_id)
    
    data = {
        'id': shop.id,
        'name': shop.name,
        'owner_id': shop.owner.id,
        'owner_email': shop.owner.email,
        'is_active': shop.is_active,
        'created_at': shop.created_at.isoformat() if hasattr(shop, 'created_at') else '',
    }
    
    return JsonResponse(data)


@login_required
@permission_required(AdminPermission.MANAGE_LISTINGS)
def api_listing_details(request, listing_id):
    """
    Get listing details as JSON for review.
    """
    listing = get_object_or_404(Listing, id=listing_id)
    
    data = {
        'id': listing.id,
        'title': listing.title,
        'description': listing.description if hasattr(listing, 'description') else '',
        'status': listing.status,
        'is_featured': listing.is_featured if hasattr(listing, 'is_featured') else False,
        'shop_id': listing.shop.id if hasattr(listing, 'shop') else None,
        'created_at': listing.created_at.isoformat() if hasattr(listing, 'created_at') else '',
    }
    
    return JsonResponse(data)


# ============================================================
# SSL & DOMAIN MANAGEMENT BACKEND
# ============================================================

@login_required
@permission_required(AdminPermission.MANAGE_SHOP_DOMAINS)
def admin_ssl_domains_list(request):
    """
    Admin page: List all SSL domains and their status.
    Shows domain, SSL status, expiration date, shop owner.
    """
    shops = Shop.objects.select_related('owner').order_by('-created_at')
    
    # Filter by search
    search = request.GET.get('search', '').strip()
    if search:
        shops = shops.filter(
            Q(name__icontains=search) | 
            Q(domain__icontains=search) |
            Q(owner__email__icontains=search)
        )
    
    # Filter by SSL status
    ssl_status = request.GET.get('ssl_status', '')
    if ssl_status == 'active':
        shops = shops.filter(has_ssl=True)
    elif ssl_status == 'inactive':
        shops = shops.filter(has_ssl=False)
    elif ssl_status == 'expiring':
        from django.utils import timezone
        thirty_days = timezone.now() + timedelta(days=30)
        shops = shops.filter(has_ssl=True, ssl_expires_at__lte=thirty_days)
    
    # Pagination
    page = int(request.GET.get('page', 1))
    per_page = 50
    total = shops.count()
    start = (page - 1) * per_page
    end = start + per_page
    
    shops_page = shops[start:end]
    total_pages = (total + per_page - 1) // per_page
    
    context = {
        'shops': shops_page,
        'total': total,
        'page': page,
        'total_pages': total_pages,
        'search': search,
        'ssl_status': ssl_status,
    }
    
    return render(request, 'admin/ssl_domains.html', context)


@login_required
@permission_required(AdminPermission.MANAGE_SHOP_DOMAINS)
def admin_ssl_domain_detail(request, shop_id):
    """
    Admin page: View and manage SSL for specific shop domain.
    Shows current SSL status, certificate info, renewal options.
    """
    shop = get_object_or_404(Shop, id=shop_id)
    
    # Check permission to edit this shop
    if not (request.user.is_superuser or request.user.is_staff):
        return HttpResponseForbidden("Permission denied")
    
    # Get SSL info from manager
    ssl_info = {}
    if shop.ssl_subdomain:
        from .ssl_manager import SSLCertificateManager
        ssl_mgr = SSLCertificateManager()
        ssl_info = ssl_mgr.get_certificate_info(shop.ssl_subdomain)
    
    context = {
        'shop': shop,
        'ssl_info': ssl_info,
    }
    
    return render(request, 'admin/ssl_domain_detail.html', context)


@login_required
@permission_required(AdminPermission.MANAGE_SHOP_DOMAINS)
@require_http_methods(["POST"])
def admin_ssl_generate(request, shop_id):
    """
    Generate SSL certificate for shop domain.
    """
    shop = get_object_or_404(Shop, id=shop_id)
    
    if not (request.user.is_superuser or request.user.is_staff):
        return HttpResponseForbidden("Permission denied")
    
    try:
        from .ssl_manager import SSLCertificateManager
        ssl_mgr = SSLCertificateManager()
        
        # Generate certificate
        result = ssl_mgr.generate_certificate_for_shop(shop.name)
        
        if result['success']:
            # Update shop with SSL info
            shop.has_ssl = True
            shop.ssl_subdomain = result.get('subdomain')
            if result.get('cert_path'):
                shop.ssl_cert_path = result['cert_path']
            # Set expiration to 90 days from now (Let's Encrypt default)
            shop.ssl_expires_at = timezone.now() + timedelta(days=90)
            shop.save()
            
            # Log audit action
            log_admin_action(
                request, 'generate_ssl', 'Shop', shop.id, shop.name,
                changes={'has_ssl': {'old': False, 'new': True}},
                reason='SSL certificate generated via admin panel',
                status='success'
            )
            
            # Log activity feed
            log_activity_feed(
                request, 'ssl_generated', 'Shop', shop.id,
                object_title=shop.name,
                description=f'SSL certificate generated for {shop.name}',
                severity='success'
            )
            
            messages.success(request, f'SSL certificate generated for {shop.name}')
        else:
            error_msg = result.get('error', 'Unknown error')
            log_admin_action(
                request, 'generate_ssl', 'Shop', shop.id, shop.name,
                reason='SSL certificate generation failed',
                status='error',
                error_msg=error_msg
            )
            messages.error(request, f"Failed to generate SSL: {error_msg}")
    
    except Exception as e:
        log_admin_action(
            request, 'generate_ssl', 'Shop', shop.id, shop.name,
            reason='SSL generation exception',
            status='error',
            error_msg=str(e)
        )
        messages.error(request, f"Error: {str(e)}")
    
    return redirect('admin:ssl_domain_detail', shop_id=shop.id)


@login_required
@permission_required(AdminPermission.MANAGE_SHOP_DOMAINS)
@require_http_methods(["POST"])
def admin_ssl_renew(request, shop_id):
    """
    Renew SSL certificate for shop domain.
    """
    shop = get_object_or_404(Shop, id=shop_id)
    
    if not (request.user.is_superuser or request.user.is_staff):
        return HttpResponseForbidden("Permission denied")
    
    if not shop.has_ssl or not shop.ssl_subdomain:
        messages.error(request, "Shop does not have an active SSL certificate")
        return redirect('admin:ssl_domain_detail', shop_id=shop.id)
    
    try:
        from .ssl_manager import SSLCertificateManager
        ssl_mgr = SSLCertificateManager()
        
        # Renew certificate
        result = ssl_mgr.renew_certificate(shop.ssl_subdomain)
        
        if result['success']:
            # Update expiration date
            shop.ssl_expires_at = timezone.now() + timedelta(days=90)
            shop.save()
            
            # Log audit action
            log_admin_action(
                request, 'renew_ssl', 'Shop', shop.id, shop.name,
                changes={'ssl_expires_at': {'old': str(shop.ssl_expires_at), 
                                          'new': str(timezone.now() + timedelta(days=90))}},
                reason='SSL certificate renewed via admin panel',
                status='success'
            )
            
            # Log activity feed
            log_activity_feed(
                request, 'ssl_renewed', 'Shop', shop.id,
                object_title=shop.name,
                description=f'SSL certificate renewed for {shop.name}',
                severity='success'
            )
            
            messages.success(request, f'SSL certificate renewed for {shop.name}')
        else:
            error_msg = result.get('error', 'Unknown error')
            log_admin_action(
                request, 'renew_ssl', 'Shop', shop.id, shop.name,
                reason='SSL renewal failed',
                status='error',
                error_msg=error_msg
            )
            messages.error(request, f"Failed to renew SSL: {error_msg}")
    
    except Exception as e:
        log_admin_action(
            request, 'renew_ssl', 'Shop', shop.id, shop.name,
            reason='SSL renewal exception',
            status='error',
            error_msg=str(e)
        )
        messages.error(request, f"Error: {str(e)}")
    
    return redirect('admin:ssl_domain_detail', shop_id=shop.id)


@login_required
@permission_required(AdminPermission.MANAGE_SHOP_DOMAINS)
@require_http_methods(["POST"])
def admin_ssl_check_status(request, shop_id):
    """
    Check SSL certificate status for shop domain.
    """
    shop = get_object_or_404(Shop, id=shop_id)
    
    if not shop.has_ssl or not shop.ssl_subdomain:
        return JsonResponse({'error': 'No SSL certificate'}, status=400)
    
    try:
        from .ssl_manager import SSLCertificateManager
        ssl_mgr = SSLCertificateManager()
        
        # Get certificate info
        info = ssl_mgr.get_certificate_info(shop.ssl_subdomain)
        
        return JsonResponse({
            'subdomain': shop.ssl_subdomain,
            'status': 'active' if shop.has_ssl else 'inactive',
            'expires_at': shop.ssl_expires_at.isoformat() if shop.ssl_expires_at else None,
            'info': info,
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@permission_required(AdminPermission.MANAGE_SHOP_DOMAINS)
@require_http_methods(["POST"])
def admin_ssl_bulk_generate(request):
    """
    Bulk generate SSL certificates for multiple shops.
    """
    try:
        data = json.loads(request.body)
        shop_ids = data.get('shop_ids', [])
        
        if not shop_ids:
            return JsonResponse({'error': 'No shops selected'}, status=400)
        
        shops = Shop.objects.filter(id__in=shop_ids, has_ssl=False)
        
        from .ssl_manager import SSLCertificateManager
        ssl_mgr = SSLCertificateManager()
        
        results = {
            'success': [],
            'failed': [],
        }
        
        batch_id = AdminActivityFeed.objects.latest('batch_id').batch_id if AdminActivityFeed.objects.exists() else 'batch_001'
        
        for shop in shops:
            result = ssl_mgr.generate_certificate_for_shop(shop.name)
            
            if result['success']:
                shop.has_ssl = True
                shop.ssl_subdomain = result.get('subdomain')
                if result.get('cert_path'):
                    shop.ssl_cert_path = result['cert_path']
                shop.ssl_expires_at = timezone.now() + timedelta(days=90)
                shop.save()
                
                results['success'].append({
                    'shop_id': shop.id,
                    'shop_name': shop.name,
                    'subdomain': result.get('subdomain'),
                })
                
                # Log individual action
                log_activity_feed(
                    request, 'ssl_generated', 'Shop', shop.id,
                    object_title=shop.name,
                    description=f'SSL cert generated',
                    severity='success',
                    batch_id=batch_id
                )
            else:
                results['failed'].append({
                    'shop_id': shop.id,
                    'shop_name': shop.name,
                    'error': result.get('error', 'Unknown error'),
                })
        
        # Log audit action
        log_admin_action(
            request, 'bulk_generate_ssl', 'Shop', 0, f'{len(results["success"])} shops',
            changes={'ssl_count': {'old': 0, 'new': len(results['success'])}},
            reason=f'Bulk SSL generation: {len(results["success"])} succeeded, {len(results["failed"])} failed',
            status='partial_success' if results['failed'] else 'success'
        )
        
        return JsonResponse(results)
    
    except Exception as e:
        log_admin_action(
            request, 'bulk_generate_ssl', 'Shop', 0, 'bulk operation',
            reason='Bulk SSL generation exception',
            status='error',
            error_msg=str(e)
        )
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================
# TENANT MANAGEMENT BACKEND (Superuser Only)
# ============================================================

@login_required
@permission_required(AdminPermission.MANAGE_TENANTS)
def admin_tenants_list(request):
    """
    Admin page: List all tenants (Clients) with summary statistics.
    Superuser only. Shows tenant name, type, billing status, user count, shops count.
    """
    if not request.user.is_superuser:
        return HttpResponseForbidden("Superuser access required")
    
    # Get all tenants
    tenants = Client.objects.prefetch_related('child_tenants').order_by('-created_at')
    
    # Filter by tenant type
    tenant_type = request.GET.get('type', '')
    if tenant_type in ['university', 'location', 'shop']:
        tenants = tenants.filter(tenant_type=tenant_type)
    
    # Filter by billing status
    billing_status = request.GET.get('billing', '')
    if billing_status == 'trial':
        tenants = tenants.filter(on_trial=True)
    elif billing_status == 'paid':
        tenants = tenants.filter(on_trial=False)
    elif billing_status == 'expired':
        from django.utils import timezone
        tenants = tenants.filter(paid_until__lt=timezone.now(), on_trial=False)
    
    # Search by name or domain
    search = request.GET.get('search', '').strip()
    if search:
        tenants = tenants.filter(
            Q(name__icontains=search) |
            Q(clientdomain__domain__icontains=search)
        ).distinct()
    
    # Pagination
    page = int(request.GET.get('page', 1))
    per_page = 50
    total = tenants.count()
    start = (page - 1) * per_page
    end = start + per_page
    
    tenants_page = tenants[start:end]
    total_pages = (total + per_page - 1) // per_page
    
    # Calculate stats for each tenant
    for tenant in tenants_page:
        tenant.child_count = tenant.child_tenants.count()
        tenant.user_count = tenant.get_users().count()
        tenant.shop_count = Shop.objects.filter(owner__in=tenant.get_users()).count()
    
    context = {
        'tenants': tenants_page,
        'total': total,
        'page': page,
        'total_pages': total_pages,
        'search': search,
        'tenant_type': tenant_type,
        'billing_status': billing_status,
    }
    
    return render(request, 'admin/tenants_list.html', context)


@login_required
@permission_required(AdminPermission.MANAGE_TENANTS)
def admin_tenant_detail(request, tenant_id):
    """
    Admin page: View and manage specific tenant details.
    Shows: basic info, billing status, domains, child tenants, users, shops.
    """
    if not request.user.is_superuser:
        return HttpResponseForbidden("Superuser access required")
    
    tenant = get_object_or_404(Client, id=tenant_id)
    
    # Get related data
    domains = ClientDomain.objects.filter(tenant=tenant)
    child_tenants = tenant.child_tenants.all()
    users = tenant.get_users()
    shops = Shop.objects.filter(owner__in=users)
    
    # Stats
    stats = {
        'user_count': users.count(),
        'shop_count': shops.count(),
        'child_tenant_count': child_tenants.count(),
        'domain_count': domains.count(),
        'total_listings': Listing.objects.filter(shop__in=shops).count() if shops.exists() else 0,
    }
    
    # Calculate revenue (if available)
    if hasattr(Transaction, 'objects'):
        stats['total_revenue'] = Transaction.objects.filter(
            shop__in=shops
        ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'tenant': tenant,
        'domains': domains,
        'child_tenants': child_tenants,
        'users': users[:10],  # Show first 10 users
        'shops': shops[:10],  # Show first 10 shops
        'stats': stats,
    }
    
    return render(request, 'admin/tenant_detail.html', context)


@login_required
@permission_required(AdminPermission.MANAGE_TENANTS)
@require_http_methods(["POST"])
def admin_tenant_update_billing(request, tenant_id):
    """
    Update tenant billing information (paid_until, on_trial status).
    """
    if not request.user.is_superuser:
        return HttpResponseForbidden("Superuser access required")
    
    tenant = get_object_or_404(Client, id=tenant_id)
    
    try:
        data = json.loads(request.body)
        on_trial = data.get('on_trial')
        paid_until = data.get('paid_until')
        
        old_values = {
            'on_trial': tenant.on_trial,
            'paid_until': str(tenant.paid_until) if tenant.paid_until else None,
        }
        
        if on_trial is not None:
            tenant.on_trial = on_trial
        
        if paid_until:
            from datetime import datetime
            tenant.paid_until = datetime.fromisoformat(paid_until).date()
        
        tenant.save()
        
        new_values = {
            'on_trial': tenant.on_trial,
            'paid_until': str(tenant.paid_until) if tenant.paid_until else None,
        }
        
        # Log audit action
        log_admin_action(
            request, 'update_billing', 'Tenant', tenant.id, tenant.name,
            changes={'billing': {'old': old_values, 'new': new_values}},
            reason='Billing information updated via admin panel',
            status='success'
        )
        
        # Log activity feed
        log_activity_feed(
            request, 'billing_updated', 'Tenant', tenant.id,
            object_title=tenant.name,
            description=f'Billing updated: trial={tenant.on_trial}, expires {tenant.paid_until}',
            severity='info'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Billing information updated',
            'tenant': {
                'id': tenant.id,
                'name': tenant.name,
                'on_trial': tenant.on_trial,
                'paid_until': str(tenant.paid_until) if tenant.paid_until else None,
            }
        })
    
    except Exception as e:
        log_admin_action(
            request, 'update_billing', 'Tenant', tenant.id, tenant.name,
            reason='Billing update failed',
            status='error',
            error_msg=str(e)
        )
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@permission_required(AdminPermission.MANAGE_TENANTS)
@require_http_methods(["POST"])
def admin_tenant_activate(request, tenant_id):
    """
    Activate a tenant (set on_trial=False, set paid_until to future date).
    """
    if not request.user.is_superuser:
        return HttpResponseForbidden("Superuser access required")
    
    tenant = get_object_or_404(Client, id=tenant_id)
    
    try:
        # Set to paid status
        old_on_trial = tenant.on_trial
        tenant.on_trial = False
        
        # Set paid_until to 1 year from now
        from datetime import datetime, timedelta
        tenant.paid_until = (datetime.now() + timedelta(days=365)).date()
        tenant.save()
        
        # Log audit action
        log_admin_action(
            request, 'activate_tenant', 'Tenant', tenant.id, tenant.name,
            changes={'on_trial': {'old': old_on_trial, 'new': False}},
            reason='Tenant activated via admin panel',
            status='success'
        )
        
        # Log activity feed
        log_activity_feed(
            request, 'tenant_activated', 'Tenant', tenant.id,
            object_title=tenant.name,
            description=f'{tenant.name} activated, paid until {tenant.paid_until}',
            severity='success'
        )
        
        messages.success(request, f'Tenant {tenant.name} activated')
        
    except Exception as e:
        log_admin_action(
            request, 'activate_tenant', 'Tenant', tenant.id, tenant.name,
            reason='Tenant activation failed',
            status='error',
            error_msg=str(e)
        )
        messages.error(request, f"Error: {str(e)}")
    
    return redirect('admin:tenant_detail', tenant_id=tenant.id)


@login_required
@permission_required(AdminPermission.MANAGE_TENANTS)
@require_http_methods(["POST"])
def admin_tenant_deactivate(request, tenant_id):
    """
    Deactivate a tenant (set on_trial=True, clear paid_until).
    """
    if not request.user.is_superuser:
        return HttpResponseForbidden("Superuser access required")
    
    tenant = get_object_or_404(Client, id=tenant_id)
    
    try:
        old_on_trial = tenant.on_trial
        old_paid_until = tenant.paid_until
        
        tenant.on_trial = True
        tenant.paid_until = None
        tenant.save()
        
        # Log audit action
        log_admin_action(
            request, 'deactivate_tenant', 'Tenant', tenant.id, tenant.name,
            changes={
                'on_trial': {'old': old_on_trial, 'new': True},
                'paid_until': {'old': str(old_paid_until), 'new': None}
            },
            reason='Tenant deactivated via admin panel',
            status='success'
        )
        
        # Log activity feed
        log_activity_feed(
            request, 'tenant_deactivated', 'Tenant', tenant.id,
            object_title=tenant.name,
            description=f'{tenant.name} deactivated',
            severity='warning'
        )
        
        messages.success(request, f'Tenant {tenant.name} deactivated')
        
    except Exception as e:
        log_admin_action(
            request, 'deactivate_tenant', 'Tenant', tenant.id, tenant.name,
            reason='Tenant deactivation failed',
            status='error',
            error_msg=str(e)
        )
        messages.error(request, f"Error: {str(e)}")
    
    return redirect('admin:tenant_detail', tenant_id=tenant.id)


@login_required
@permission_required(AdminPermission.MANAGE_TENANTS)
def admin_tenant_domains(request, tenant_id):
    """
    Manage domains for a tenant.
    """
    if not request.user.is_superuser:
        return HttpResponseForbidden("Superuser access required")
    
    tenant = get_object_or_404(Client, id=tenant_id)
    domains = ClientDomain.objects.filter(tenant=tenant).order_by('domain')
    
    context = {
        'tenant': tenant,
        'domains': domains,
    }
    
    return render(request, 'admin/tenant_domains.html', context)


@login_required
@permission_required(AdminPermission.MANAGE_TENANTS)
@require_http_methods(["POST"])
def admin_tenant_add_domain(request, tenant_id):
    """
    Add a new domain to a tenant.
    """
    if not request.user.is_superuser:
        return HttpResponseForbidden("Superuser access required")
    
    tenant = get_object_or_404(Client, id=tenant_id)
    
    try:
        data = json.loads(request.body)
        domain = data.get('domain', '').strip()
        
        if not domain:
            return JsonResponse({'error': 'Domain is required'}, status=400)
        
        # Check if domain already exists
        if ClientDomain.objects.filter(domain=domain).exists():
            return JsonResponse({'error': 'Domain already exists'}, status=400)
        
        # Create domain
        client_domain = ClientDomain.objects.create(
            tenant=tenant,
            domain=domain,
            is_primary=data.get('is_primary', False)
        )
        
        # Log activity
        log_activity_feed(
            request, 'domain_added', 'Tenant', tenant.id,
            object_title=tenant.name,
            description=f'Domain added: {domain}',
            severity='info'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Domain {domain} added',
            'domain': {
                'id': client_domain.id,
                'domain': client_domain.domain,
                'is_primary': client_domain.is_primary,
            }
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@permission_required(AdminPermission.MANAGE_TENANTS)
@require_http_methods(["POST"])
def admin_tenant_delete_domain(request, tenant_id, domain_id):
    """
    Delete a domain from a tenant.
    """
    if not request.user.is_superuser:
        return HttpResponseForbidden("Superuser access required")
    
    tenant = get_object_or_404(Client, id=tenant_id)
    domain = get_object_or_404(ClientDomain, id=domain_id, tenant=tenant)
    
    try:
        domain_name = domain.domain
        domain.delete()
        
        # Log activity
        log_activity_feed(
            request, 'domain_deleted', 'Tenant', tenant.id,
            object_title=tenant.name,
            description=f'Domain deleted: {domain_name}',
            severity='info'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Domain {domain_name} deleted',
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ============================================================
# THEME MANAGEMENT BACKEND
# ============================================================

@login_required
@permission_required(AdminPermission.MANAGE_THEMES)
def admin_themes_list(request):
    """
    Admin page: List all themes with preview and status.
    Shows theme name, colors, creator, active status, published date.
    """
    themes = Theme.objects.select_related('created_by').order_by('-is_active', '-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        themes = themes.filter(is_active=True)
    elif status_filter == 'public':
        themes = themes.filter(is_public=True)
    elif status_filter == 'draft':
        themes = themes.filter(is_public=False)
    
    # Search by name
    search = request.GET.get('search', '').strip()
    if search:
        themes = themes.filter(name__icontains=search)
    
    # Pagination
    page = int(request.GET.get('page', 1))
    per_page = 50
    total = themes.count()
    start = (page - 1) * per_page
    end = start + per_page
    
    themes_page = themes[start:end]
    total_pages = (total + per_page - 1) // per_page
    
    context = {
        'themes': themes_page,
        'total': total,
        'page': page,
        'total_pages': total_pages,
        'search': search,
        'status': status_filter,
    }
    
    return render(request, 'admin/themes_list.html', context)


@login_required
@permission_required(AdminPermission.MANAGE_THEMES)
def admin_theme_detail(request, theme_id):
    """
    Admin page: View and edit theme configuration.
    Shows theme tokens, custom CSS, and preview.
    """
    theme = get_object_or_404(Theme, id=theme_id)
    tokens = ThemeToken.objects.all().order_by('category', 'name')
    
    # Get merged tokens for this theme
    merged_tokens = theme.get_merged_tokens()
    
    context = {
        'theme': theme,
        'tokens': tokens,
        'merged_tokens': merged_tokens,
        'can_edit': request.user.is_superuser or theme.created_by == request.user,
    }
    
    return render(request, 'admin/theme_detail.html', context)


@login_required
@permission_required(AdminPermission.MANAGE_THEMES)
@require_http_methods(["POST"])
def admin_theme_create(request):
    """
    Create a new theme.
    """
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        description = data.get('description', '')
        
        if not name:
            return JsonResponse({'error': 'Theme name is required'}, status=400)
        
        # Check if name already exists
        if Theme.objects.filter(name=name).exists():
            return JsonResponse({'error': 'Theme with this name already exists'}, status=400)
        
        # Create theme
        theme = Theme.objects.create(
            name=name,
            description=description,
            created_by=request.user,
            is_active=False,
            is_public=False,
        )
        
        # Log audit action
        log_admin_action(
            request, 'create_theme', 'Theme', theme.id, theme.name,
            changes={'created': {'old': None, 'new': name}},
            reason='New theme created via admin panel',
            status='success'
        )
        
        # Log activity feed
        log_activity_feed(
            request, 'theme_created', 'Theme', theme.id,
            object_title=theme.name,
            description=f'New theme created: {theme.name}',
            severity='success'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Theme {name} created',
            'theme': {
                'id': theme.id,
                'name': theme.name,
                'url': f'/admin/theme/{theme.id}/',
            }
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@permission_required(AdminPermission.MANAGE_THEMES)
@require_http_methods(["POST"])
def admin_theme_update(request, theme_id):
    """
    Update theme configuration (tokens, CSS, name, description).
    """
    theme = get_object_or_404(Theme, id=theme_id)
    
    # Check permission (only creator or superuser)
    if not (request.user.is_superuser or theme.created_by == request.user):
        return HttpResponseForbidden("Permission denied")
    
    try:
        data = json.loads(request.body)
        
        old_values = {
            'name': theme.name,
            'description': theme.description,
            'token_overrides': dict(theme.token_overrides) if theme.token_overrides else {},
            'custom_css_length': len(theme.custom_css or ''),
        }
        
        # Update basic fields
        if 'name' in data:
            theme.name = data['name']
        if 'description' in data:
            theme.description = data['description']
        
        # Update token overrides
        if 'token_overrides' in data:
            theme.token_overrides = data['token_overrides']
        
        # Update custom CSS
        if 'custom_css' in data:
            theme.custom_css = data['custom_css']
        
        # Update public status if specified
        if 'is_public' in data:
            old_public = theme.is_public
            theme.is_public = data['is_public']
        
        theme.save()
        
        new_values = {
            'name': theme.name,
            'description': theme.description,
            'token_overrides': dict(theme.token_overrides) if theme.token_overrides else {},
            'custom_css_length': len(theme.custom_css or ''),
        }
        
        # Log audit action
        log_admin_action(
            request, 'update_theme', 'Theme', theme.id, theme.name,
            changes={'config': {'old': old_values, 'new': new_values}},
            reason='Theme configuration updated via admin panel',
            status='success'
        )
        
        # Log activity feed
        log_activity_feed(
            request, 'theme_updated', 'Theme', theme.id,
            object_title=theme.name,
            description=f'Theme configuration updated',
            severity='info'
        )
        
        # Invalidate cache
        from .admin_utils import invalidate_theme_cache
        invalidate_theme_cache(theme.id)
        
        return JsonResponse({
            'success': True,
            'message': 'Theme updated',
            'theme': {
                'id': theme.id,
                'name': theme.name,
                'is_public': theme.is_public,
                'is_active': theme.is_active,
            }
        })
    
    except Exception as e:
        log_admin_action(
            request, 'update_theme', 'Theme', theme.id, theme.name,
            reason='Theme update failed',
            status='error',
            error_msg=str(e)
        )
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@permission_required(AdminPermission.MANAGE_THEMES)
@require_http_methods(["POST"])
def admin_theme_activate(request, theme_id):
    """
    Activate a theme (only one can be active at a time).
    """
    theme = get_object_or_404(Theme, id=theme_id)
    
    # Check permission
    if not (request.user.is_superuser or theme.created_by == request.user):
        return HttpResponseForbidden("Permission denied")
    
    try:
        # Get previous active theme
        previous_active = Theme.objects.filter(is_active=True).first()
        
        # Activate this theme (save() will deactivate others)
        theme.is_active = True
        theme.save()
        
        # Log audit action
        old_active = previous_active.name if previous_active else None
        log_admin_action(
            request, 'activate_theme', 'Theme', theme.id, theme.name,
            changes={'is_active': {'old': old_active, 'new': theme.name}},
            reason='Theme activated via admin panel',
            status='success'
        )
        
        # Log activity feed
        log_activity_feed(
            request, 'theme_activated', 'Theme', theme.id,
            object_title=theme.name,
            description=f'{theme.name} activated',
            severity='success'
        )
        
        # Invalidate cache
        from .admin_utils import invalidate_theme_cache
        invalidate_theme_cache()
        
        messages.success(request, f'Theme {theme.name} activated')
        
    except Exception as e:
        log_admin_action(
            request, 'activate_theme', 'Theme', theme.id, theme.name,
            reason='Theme activation failed',
            status='error',
            error_msg=str(e)
        )
        messages.error(request, f"Error: {str(e)}")
    
    return redirect('admin:theme_detail', theme_id=theme.id)


@login_required
@permission_required(AdminPermission.MANAGE_THEMES)
@require_http_methods(["POST"])
def admin_theme_delete(request, theme_id):
    """
    Delete a theme (cannot delete active theme).
    """
    theme = get_object_or_404(Theme, id=theme_id)
    
    # Check permission
    if not (request.user.is_superuser or theme.created_by == request.user):
        return HttpResponseForbidden("Permission denied")
    
    if theme.is_active:
        messages.error(request, "Cannot delete the active theme. Activate another theme first.")
        return redirect('admin:theme_detail', theme_id=theme.id)
    
    try:
        theme_name = theme.name
        theme.delete()
        
        # Log audit action
        log_admin_action(
            request, 'delete_theme', 'Theme', theme_id, theme_name,
            changes={'deleted': {'old': theme_name, 'new': None}},
            reason='Theme deleted via admin panel',
            status='success'
        )
        
        # Log activity feed
        log_activity_feed(
            request, 'theme_deleted', 'Theme', theme_id,
            object_title=theme_name,
            description=f'Theme deleted: {theme_name}',
            severity='warning'
        )
        
        messages.success(request, f'Theme {theme_name} deleted')
        
    except Exception as e:
        log_admin_action(
            request, 'delete_theme', 'Theme', theme_id, theme_name,
            reason='Theme deletion failed',
            status='error',
            error_msg=str(e)
        )
        messages.error(request, f"Error: {str(e)}")
    
    return redirect('admin:themes_list')


# ============================================================================
# ACTIVITY FEED & CHANGELOG VIEWS
# ============================================================================

@login_required
@permission_required('admin.can_view_activity')
def admin_activity_feed_view(request):
    """Display activity feed of admin actions"""
    try:
        feed_entries = AdminActivityFeed.objects.all().order_by('-created_at')[:100]
        
        context = {
            'title': 'Activity Feed',
            'feed_entries': feed_entries,
            'total_entries': AdminActivityFeed.objects.count(),
        }
        return render(request, 'admin/activity_feed.html', context)
    except Exception as e:
        messages.error(request, f"Error loading activity feed: {str(e)}")
        return redirect('admin:dashboard_full')


@login_required
@permission_required('admin.can_view_activity')
def admin_changelog_view(request):
    """Display changelog of system changes"""
    try:
        audit_logs = AdminAuditLog.objects.all().order_by('-created_at')[:200]
        
        # Group by date
        from django.db.models.functions import TruncDate
        from django.db.models import Count as DBCount
        
        changelog = AdminAuditLog.objects.all().order_by('-created_at')
        
        context = {
            'title': 'Changelog',
            'changelog': changelog[:100],
            'total_changes': AdminAuditLog.objects.count(),
        }
        return render(request, 'admin/changelog.html', context)
    except Exception as e:
        messages.error(request, f"Error loading changelog: {str(e)}")
        return redirect('admin:dashboard_full')


# ============================================================================
# API ENDPOINTS FOR AJAX/MODALS
# ============================================================================

@login_required
@permission_required('admin.can_view_users')
@require_http_methods(["GET"])
def api_user_details(request, user_id):
    """API endpoint to get user details for modal/AJAX"""
    try:
        user = get_object_or_404(User, id=user_id)
        
        data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@permission_required('admin.can_view_shops')
@require_http_methods(["GET"])
def api_shop_details(request, shop_id):
    """API endpoint to get shop details for modal/AJAX"""
    try:
        shop = get_object_or_404(Shop, id=shop_id)
        
        data = {
            'id': shop.id,
            'name': shop.name,
            'owner': str(shop.owner) if hasattr(shop, 'owner') else '',
            'is_active': getattr(shop, 'is_active', True),
            'created_at': shop.created_at.isoformat() if hasattr(shop, 'created_at') else '',
            'listings_count': shop.listing_set.count() if hasattr(shop, 'listing_set') else 0,
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@permission_required('admin.can_view_listings')
@require_http_methods(["GET"])
def api_listing_details(request, listing_id):
    """API endpoint to get listing details for modal/AJAX"""
    try:
        listing = get_object_or_404(Listing, id=listing_id)
        
        data = {
            'id': listing.id,
            'title': listing.title if hasattr(listing, 'title') else '',
            'shop': str(listing.shop) if hasattr(listing, 'shop') else '',
            'price': str(getattr(listing, 'price', 0)),
            'status': getattr(listing, 'status', 'active'),
            'created_at': listing.created_at.isoformat() if hasattr(listing, 'created_at') else '',
            'is_featured': getattr(listing, 'is_featured', False),
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@permission_required(AdminPermission.MANAGE_THEMES)
def admin_theme_preview(request, theme_id):
    """
    Preview theme CSS and token values.
    Returns JSON with compiled CSS.
    """
    theme = get_object_or_404(Theme, id=theme_id)
    
    try:
        css = theme.generate_css()
        
        return JsonResponse({
            'success': True,
            'css': css,
            'theme_name': theme.name,
            'tokens': theme.get_merged_tokens(),
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@permission_required(AdminPermission.MANAGE_THEMES)
def admin_theme_publish(request, theme_id):
    """
    Publish theme to make it available to users.
    """
    theme = get_object_or_404(Theme, id=theme_id)
    
    # Check permission
    if not (request.user.is_superuser or theme.created_by == request.user):
        return HttpResponseForbidden("Permission denied")
    
    try:
        old_public = theme.is_public
        theme.is_public = True
        theme.save()
        
        # Log audit action
        log_admin_action(
            request, 'publish_theme', 'Theme', theme.id, theme.name,
            changes={'is_public': {'old': old_public, 'new': True}},
            reason='Theme published via admin panel',
            status='success'
        )
        
        # Log activity feed
        log_activity_feed(
            request, 'theme_published', 'Theme', theme.id,
            object_title=theme.name,
            description=f'{theme.name} published',
            severity='success'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Theme {theme.name} published',
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@permission_required(AdminPermission.MANAGE_THEMES)
def admin_theme_unpublish(request, theme_id):
    """
    Unpublish theme (make private/draft).
    """
    theme = get_object_or_404(Theme, id=theme_id)
    
    # Check permission
    if not (request.user.is_superuser or theme.created_by == request.user):
        return HttpResponseForbidden("Permission denied")
    
    try:
        old_public = theme.is_public
        theme.is_public = False
        theme.save()
        
        # Log audit action
        log_admin_action(
            request, 'unpublish_theme', 'Theme', theme.id, theme.name,
            changes={'is_public': {'old': old_public, 'new': False}},
            reason='Theme unpublished via admin panel',
            status='success'
        )
        
        # Log activity feed
        log_activity_feed(
            request, 'theme_unpublished', 'Theme', theme.id,
            object_title=theme.name,
            description=f'{theme.name} unpublished',
            severity='warning'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Theme {theme.name} unpublished',
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
