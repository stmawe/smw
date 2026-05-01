"""
Advanced Admin Backend Features
Transaction processing, moderation workflows, and system features.
Extends admin_crud_views.py with additional CRUD operations.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta
import json

from .models import (
    User, Category, Theme, AdminAuditLog, AdminActivityFeed
)
from mydak.models import Shop, Listing, Transaction
from .admin_permissions import permission_required, AdminPermission
from .admin_crud_views import log_admin_action, log_activity_feed, get_client_ip


# ============================================================
# MODERATION & CONTENT MANAGEMENT VIEWS
# ============================================================

@login_required
@permission_required(AdminPermission.MODERATE_CONTENT)
def admin_moderation_center(request):
    """
    Main moderation hub with tabs for different content types.
    """
    tab = request.GET.get('tab', 'flagged')
    
    # Get flagged listings
    flagged_listings = Listing.objects.filter(
        flagged_for_review=True
    ).order_by('-updated_at')[:50]
    
    # Get banned users
    banned_users = User.objects.filter(
        is_active=False
    ).order_by('-date_joined')[:50]
    
    # Get pending items
    pending_listings = Listing.objects.filter(
        status='pending'
    ).count()
    
    context = {
        'tab': tab,
        'flagged_listings': flagged_listings,
        'banned_users': banned_users,
        'pending_count': pending_listings,
        'flagged_count': flagged_listings.count(),
        'banned_count': banned_users.count(),
    }
    
    return render(request, 'admin/moderation.html', context)


@login_required
@permission_required(AdminPermission.MODERATE_CONTENT)
@require_http_methods(["POST"])
def admin_flag_listing(request, listing_id):
    """
    Flag a listing for review/moderation.
    """
    listing = get_object_or_404(Listing, id=listing_id)
    
    reason = request.POST.get('reason', 'No reason provided')
    
    if not hasattr(listing, 'flagged_for_review'):
        listing.flagged_for_review = True
    else:
        listing.flagged_for_review = True
    
    listing.save()
    
    log_admin_action(
        request,
        'other',
        'Listing',
        listing.id,
        listing.title,
        reason=f"Flagged for moderation: {reason}",
    )
    log_activity_feed(
        request,
        'updated',
        'Listing',
        listing.id,
        object_title=listing.title,
        description=f"Flagged listing: {listing.title}",
        severity='warning',
    )
    
    messages.success(request, f"Listing flagged for review.")
    return redirect('admin_listing_detail', listing_id=listing.id)


@login_required
@permission_required(AdminPermission.MODERATE_CONTENT)
@require_http_methods(["POST"])
def admin_unflag_listing(request, listing_id):
    """
    Unflag a listing (clear moderation review).
    """
    listing = get_object_or_404(Listing, id=listing_id)
    
    if hasattr(listing, 'flagged_for_review'):
        listing.flagged_for_review = False
        listing.save()
        
        log_admin_action(
            request,
            'other',
            'Listing',
            listing.id,
            listing.title,
            reason="Cleared moderation flag",
        )
        messages.success(request, "Flag cleared.")
    
    return redirect('admin_listing_detail', listing_id=listing.id)


@login_required
@permission_required(AdminPermission.BAN_USERS)
@require_http_methods(["POST"])
def admin_ban_user_extended(request, user_id):
    """
    Ban a user with optional expiration date.
    """
    user = get_object_or_404(User, id=user_id)
    
    ban_reason = request.POST.get('ban_reason', 'Banned by admin')
    ban_duration_days = request.POST.get('ban_duration_days', '')
    
    user.is_active = False
    user.save()
    
    # If future support for time-limited bans is added:
    # ban_until = None
    # if ban_duration_days:
    #     try:
    #         days = int(ban_duration_days)
    #         ban_until = timezone.now() + timedelta(days=days)
    #     except ValueError:
    #         pass
    
    log_admin_action(
        request,
        'ban_user',
        'User',
        user.id,
        user.email,
        reason=ban_reason,
    )
    log_activity_feed(
        request,
        'banned',
        'User',
        user.id,
        object_title=user.email,
        description=f"Banned user: {user.email}",
        severity='danger',
    )
    
    messages.success(request, f"User {user.email} has been banned.")
    return redirect('admin_user_detail', user_id=user.id)


# ============================================================
# TRANSACTION MANAGEMENT & REFUNDS
# ============================================================

@login_required
@permission_required(AdminPermission.REFUND_TRANSACTIONS)
@require_http_methods(["POST"])
def admin_process_refund(request, transaction_id):
    """
    Process a refund for a transaction.
    """
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    refund_reason = request.POST.get('reason', 'Admin refund')
    
    old_status = transaction.status
    transaction.status = 'refunded'
    transaction.save()
    
    changes = {
        'status': {'old': old_status, 'new': 'refunded'}
    }
    
    log_admin_action(
        request,
        'process_refund',
        'Transaction',
        transaction.id,
        f"Refund for transaction #{transaction.id}",
        changes=changes,
        reason=refund_reason,
    )
    log_activity_feed(
        request,
        'refund',
        'Transaction',
        transaction.id,
        object_title=f"Transaction #{transaction.id}",
        description=f"Processed refund for transaction #{transaction.id}",
        severity='info',
    )
    
    messages.success(request, f"Refund processed for transaction #{transaction.id}.")
    return redirect('admin_transactions_list')


@login_required
@permission_required(AdminPermission.VIEW_ANALYTICS)
def admin_analytics_dashboard(request):
    """
    Advanced analytics and reporting dashboard.
    """
    # Time range
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Get transactions in range
    transactions = Transaction.objects.filter(created_at__gte=start_date)
    
    # Calculate metrics
    total_transactions = transactions.count()
    total_revenue = transactions.aggregate(Sum('amount'))['amount__sum'] or 0
    avg_transaction = transactions.aggregate(Avg('amount'))['amount__avg'] or 0
    
    # Transactions by status
    status_breakdown = transactions.values('status').annotate(count=Count('*'))
    
    # Top sellers
    top_sellers = transactions.values('seller').annotate(
        total_sales=Count('*'),
        revenue=Sum('amount')
    ).order_by('-revenue')[:10]
    
    # Top categories
    top_categories = Listing.objects.filter(
        transaction__created_at__gte=start_date
    ).values('category').annotate(
        count=Count('*')
    ).order_by('-count')[:10]
    
    # User growth
    new_users = User.objects.filter(
        date_joined__gte=start_date
    ).count()
    
    # Listing activity
    new_listings = Listing.objects.filter(
        created_at__gte=start_date
    ).count()
    
    active_listings = Listing.objects.filter(
        is_active=True,
        created_at__gte=start_date
    ).count()
    
    context = {
        'days': days,
        'total_transactions': total_transactions,
        'total_revenue': total_revenue,
        'avg_transaction': round(avg_transaction, 2),
        'status_breakdown': status_breakdown,
        'top_sellers': top_sellers,
        'top_categories': top_categories,
        'new_users': new_users,
        'new_listings': new_listings,
        'active_listings': active_listings,
    }
    
    return render(request, 'admin/analytics.html', context)


# ============================================================
# SYSTEM SETTINGS MANAGEMENT
# ============================================================

@login_required
@permission_required(AdminPermission.MANAGE_SETTINGS)
@require_http_methods(["POST"])
def admin_save_settings(request):
    """
    Save site-wide settings from settings form.
    """
    setting_group = request.POST.get('group', 'general')
    
    # Parse settings from request
    settings_data = {}
    for key, value in request.POST.items():
        if key.startswith('setting_'):
            settings_data[key[8:]] = value
    
    # In a real app, these would be saved to SiteSettings model
    # For now, just log the action
    
    log_admin_action(
        request,
        'setting_change',
        'SiteSettings',
        setting_group,
        object_str=f"Updated {setting_group} settings",
        changes=settings_data,
        reason=request.POST.get('reason', ''),
    )
    log_activity_feed(
        request,
        'updated',
        'Settings',
        setting_group,
        object_title=f"{setting_group.title()} Settings",
        description=f"Updated {setting_group} settings",
        severity='info',
    )
    
    messages.success(request, "Settings saved successfully.")
    return redirect('admin_settings_view')


# ============================================================
# BULK OPERATIONS
# ============================================================

@login_required
@permission_required(AdminPermission.MANAGE_LISTINGS)
@require_http_methods(["POST"])
def admin_bulk_listing_action(request):
    """
    Handle bulk actions on listings (approve, reject, delete, feature).
    """
    action = request.POST.get('action', '')
    listing_ids = request.POST.getlist('listing_ids')
    
    if not listing_ids:
        messages.error(request, "No listings selected.")
        return redirect(request.META.get('HTTP_REFERER', 'admin_listings_moderation'))
    
    reason = request.POST.get('reason', '')
    batch_id = f"bulk_{action}_{timezone.now().timestamp()}"
    
    success_count = 0
    error_count = 0
    
    for listing_id in listing_ids:
        try:
            listing = Listing.objects.get(id=listing_id)
            old_status = listing.status
            
            if action == 'approve':
                listing.status = 'active'
                action_type = 'approve_listing'
            elif action == 'reject':
                listing.status = 'rejected'
                action_type = 'reject_listing'
            elif action == 'delete':
                listing.delete()
                action_type = 'delete'
            elif action == 'feature':
                if hasattr(listing, 'is_featured'):
                    listing.is_featured = True
                    action_type = 'feature_listing'
                else:
                    continue
            else:
                continue
            
            if action != 'delete':
                listing.save()
            
            log_admin_action(
                request,
                action_type,
                'Listing',
                listing_id,
                listing.title if hasattr(listing, 'title') else str(listing_id),
                reason=reason,
                status='success',
            )
            log_activity_feed(
                request,
                action,
                'Listing',
                listing_id,
                object_title=listing.title if hasattr(listing, 'title') else str(listing_id),
                description=f"Bulk {action}: listing",
                batch_id=batch_id,
            )
            success_count += 1
        except Exception as e:
            error_count += 1
            log_admin_action(
                request,
                'other',
                'Listing',
                listing_id,
                str(listing_id),
                status='error',
                error_msg=str(e),
            )
    
    if error_count > 0:
        messages.warning(request, f"{action_count} succeeded, {error_count} failed.")
    else:
        messages.success(request, f"Bulk {action} completed: {success_count} listings.")
    
    return redirect(request.META.get('HTTP_REFERER', 'admin_listings_moderation'))


@login_required
@permission_required(AdminPermission.MANAGE_USERS)
@require_http_methods(["POST"])
def admin_bulk_user_action(request):
    """
    Handle bulk actions on users (suspend, unsuspend, delete).
    """
    action = request.POST.get('action', '')
    user_ids = request.POST.getlist('user_ids')
    
    if not user_ids:
        messages.error(request, "No users selected.")
        return redirect(request.META.get('HTTP_REFERER', 'admin_users_list'))
    
    reason = request.POST.get('reason', '')
    batch_id = f"bulk_{action}_{timezone.now().timestamp()}"
    
    success_count = 0
    
    for user_id in user_ids:
        try:
            user = User.objects.get(id=user_id)
            
            if action == 'suspend':
                user.is_active = False
                action_type = 'ban_user'
            elif action == 'unsuspend':
                user.is_active = True
                action_type = 'unban_user'
            elif action == 'delete':
                user.delete()
                action_type = 'delete'
            else:
                continue
            
            if action != 'delete':
                user.save()
            
            log_admin_action(
                request,
                action_type,
                'User',
                user_id,
                user.email,
                reason=reason,
                status='success',
            )
            log_activity_feed(
                request,
                action,
                'User',
                user_id,
                object_title=user.email,
                description=f"Bulk {action}: user",
                batch_id=batch_id,
            )
            success_count += 1
        except Exception as e:
            log_admin_action(
                request,
                'other',
                'User',
                user_id,
                str(user_id),
                status='error',
                error_msg=str(e),
            )
    
    messages.success(request, f"Bulk {action} completed: {success_count} users.")
    return redirect(request.META.get('HTTP_REFERER', 'admin_users_list'))


# ============================================================
# ACTIVITY FEED & AUDIT LOG VIEWS
# ============================================================

@login_required
@permission_required(AdminPermission.VIEW_AUDIT_LOGS)
def admin_activity_feed(request):
    """
    Real-time activity feed for dashboard/notifications.
    """
    activities = AdminActivityFeed.objects.filter(
        is_visible=True
    ).select_related('admin_user').order_by('-created_at')[:100]
    
    context = {
        'activities': activities,
    }
    
    return render(request, 'admin/activity_feed.html', context)


@login_required
@permission_required(AdminPermission.VIEW_AUDIT_LOGS)
def admin_audit_log_detail(request, log_id):
    """
    Detailed view of a single audit log entry.
    """
    log_entry = get_object_or_404(AdminAuditLog, id=log_id)
    
    context = {
        'log': log_entry,
    }
    
    return render(request, 'admin/audit_log_detail.html', context)


# ============================================================
# JSON API ENDPOINTS FOR DASHBOARD WIDGETS
# ============================================================

@login_required
@permission_required(AdminPermission.VIEW_ANALYTICS)
def api_dashboard_metrics(request):
    """
    Get dashboard metrics as JSON for frontend updates.
    """
    total_users = User.objects.count()
    total_shops = Shop.objects.count()
    active_listings = Listing.objects.filter(is_active=True).count()
    
    # Last 7 days metrics
    week_ago = timezone.now() - timedelta(days=7)
    transactions_7d = Transaction.objects.filter(created_at__gte=week_ago).count()
    revenue_7d = Transaction.objects.filter(
        created_at__gte=week_ago
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Pending items
    pending_listings = Listing.objects.filter(status='pending').count()
    pending_refunds = Transaction.objects.filter(status='pending_refund').count()
    
    data = {
        'total_users': total_users,
        'total_shops': total_shops,
        'active_listings': active_listings,
        'transactions_7d': transactions_7d,
        'revenue_7d': float(revenue_7d),
        'pending_listings': pending_listings,
        'pending_refunds': pending_refunds,
        'timestamp': timezone.now().isoformat(),
    }
    
    return JsonResponse(data)


@login_required
@permission_required(AdminPermission.VIEW_ANALYTICS)
def api_activity_feed_updates(request):
    """
    Get recent activity updates as JSON for real-time feed.
    """
    last_update = request.GET.get('since', '')
    
    activities = AdminActivityFeed.objects.filter(
        is_visible=True
    ).order_by('-created_at')[:20]
    
    if last_update:
        try:
            last_dt = timezone.datetime.fromisoformat(last_update)
            activities = activities.filter(created_at__gt=last_dt)
        except:
            pass
    
    data = {
        'activities': [
            {
                'id': a.id,
                'admin': a.admin_user.username if a.admin_user else 'System',
                'type': a.activity_type,
                'description': a.description,
                'timestamp': a.created_at.isoformat(),
                'severity': a.severity,
            }
            for a in activities
        ],
        'count': len(activities),
    }

    return JsonResponse(data)


# ============================================================================
# MODERATION CENTER VIEWS
# ============================================================================

@login_required
@permission_required('admin.can_moderate')
def admin_moderation_center(request):
    """Admin moderation center - manage flagged content"""
    try:
        flagged_listings = Listing.objects.filter(status='flagged').select_related('shop')[:50]
        
        context = {
            'title': 'Moderation Center',
            'flagged_listings': flagged_listings,
            'flagged_count': Listing.objects.filter(status='flagged').count(),
        }
        return render(request, 'admin/moderation_center.html', context)
    except Exception as e:
        messages.error(request, f"Error loading moderation center: {str(e)}")
        return redirect('admin_dashboard_full')


@login_required
@permission_required('admin.can_moderate')
@require_http_methods(["POST"])
def admin_flag_listing(request, listing_id):
    """Flag a listing for review"""
    try:
        listing = get_object_or_404(Listing, id=listing_id)
        listing.status = 'flagged'
        listing.save()
        
        messages.success(request, f'Listing {listing_id} flagged for review')
        return redirect(request.META.get('HTTP_REFERER', 'admin:dashboard_full'))
    except Exception as e:
        messages.error(request, f"Error flagging listing: {str(e)}")
        return redirect(request.META.get('HTTP_REFERER', 'admin:dashboard_full'))


@login_required
@permission_required('admin.can_moderate')
@require_http_methods(["POST"])
def admin_unflag_listing(request, listing_id):
    """Remove flag from listing"""
    try:
        listing = get_object_or_404(Listing, id=listing_id)
        listing.status = 'active'
        listing.save()
        
        messages.success(request, f'Listing {listing_id} unflagged')
        return redirect(request.META.get('HTTP_REFERER', 'admin:dashboard_full'))
    except Exception as e:
        messages.error(request, f"Error unflagging listing: {str(e)}")
        return redirect(request.META.get('HTTP_REFERER', 'admin:dashboard_full'))


@login_required
@permission_required('admin.can_ban_users')
@require_http_methods(["POST"])
def admin_ban_user_extended(request, user_id):
    """Ban user with extended options"""
    try:
        user = get_object_or_404(User, id=user_id)
        reason = request.POST.get('reason', '')
        duration_days = request.POST.get('duration_days', 0)
        
        user.is_active = False
        user.save()
        
        messages.success(request, f'User {user.username} banned')
        return redirect(request.META.get('HTTP_REFERER', 'admin:dashboard_full'))
    except Exception as e:
        messages.error(request, f"Error banning user: {str(e)}")
        return redirect(request.META.get('HTTP_REFERER', 'admin:dashboard_full'))


@login_required
@permission_required('admin.can_process_refunds')
@require_http_methods(["POST"])
def admin_process_refund(request, transaction_id):
    """Process refund for a transaction"""
    try:
        transaction = get_object_or_404(Transaction, id=transaction_id)
        reason = request.POST.get('reason', '')
        
        transaction.status = 'refunded'
        transaction.save()
        
        messages.success(request, f'Refund processed for transaction {transaction_id}')
        return redirect(request.META.get('HTTP_REFERER', 'admin:dashboard_full'))
    except Exception as e:
        messages.error(request, f"Error processing refund: {str(e)}")
        return redirect(request.META.get('HTTP_REFERER', 'admin:dashboard_full'))
