"""
Admin M-PESA settings and management dashboard.

Handles:
- M-PESA configuration
- Transaction monitoring
- Rate limit tracking
- Admin refund processing
- Payment analytics
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings

from app.models import MpesaTransaction, AdminAuditLog
from mydak.models import Transaction

logger = logging.getLogger(__name__)


def require_admin(view_func):
    """Decorator to require admin access."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff or not request.user.is_superuser:
            return redirect('admin:index')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@require_admin
@require_http_methods(['GET'])
def mpesa_dashboard_view(request):
    """
    Main M-PESA admin dashboard with overview and stats.
    """
    # Get time range
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Transaction stats
    transactions = MpesaTransaction.objects.filter(created_at__gte=start_date)
    
    total_volume = transactions.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    
    success_count = transactions.filter(status='success').count()
    failed_count = transactions.filter(status='failed').count()
    pending_count = transactions.filter(status='pending').count()
    
    success_amount = transactions.filter(status='success').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    
    # Average transaction value
    avg_value = transactions.aggregate(
        avg=Avg('amount')
    )['avg'] or Decimal('0')
    
    # Success rate
    total_count = success_count + failed_count
    success_rate = (success_count / total_count * 100) if total_count > 0 else 0
    
    # Recent transactions
    recent = transactions.order_by('-created_at')[:10]
    
    # Rate limit info
    rate_limit_remaining = min([t.rate_limit_remaining for t in transactions if t.rate_limit_remaining]) if transactions else None
    rate_limit_total = MpesaTransaction.objects.filter(rate_limit_total__isnull=False).values_list('rate_limit_total', flat=True).first()
    
    return render(request, 'admin/mpesa/dashboard.html', {
        'total_volume': total_volume,
        'success_count': success_count,
        'failed_count': failed_count,
        'pending_count': pending_count,
        'success_amount': success_amount,
        'avg_value': avg_value,
        'success_rate': round(success_rate, 1),
        'recent': recent,
        'rate_limit_remaining': rate_limit_remaining,
        'rate_limit_total': rate_limit_total,
        'days': days,
    })


@login_required
@require_admin
@require_http_methods(['GET'])
def mpesa_transactions_view(request):
    """
    View all M-PESA transactions with filtering and search.
    """
    transactions = MpesaTransaction.objects.all().order_by('-created_at')
    
    # Filters
    status_filter = request.GET.get('status')
    if status_filter:
        transactions = transactions.filter(status=status_filter)
    
    type_filter = request.GET.get('type')
    if type_filter:
        transactions = transactions.filter(transaction_type=type_filter)
    
    # Search
    search = request.GET.get('search', '').strip()
    if search:
        transactions = transactions.filter(
            Q(phone__icontains=search) |
            Q(receipt__icontains=search) |
            Q(reference__icontains=search) |
            Q(user__username__icontains=search) |
            Q(user__email__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(transactions, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Status options
    status_choices = MpesaTransaction._meta.get_field('status').choices
    
    return render(request, 'admin/mpesa/transactions.html', {
        'page_obj': page_obj,
        'status_choices': status_choices,
        'search': search,
        'selected_status': status_filter,
        'selected_type': type_filter,
    })


@login_required
@require_admin
@require_http_methods(['GET'])
def mpesa_transaction_detail_view(request, transaction_id):
    """
    View detailed information for a specific M-PESA transaction.
    """
    transaction = get_object_or_404(MpesaTransaction, id=transaction_id)
    
    # Get linked mydak transaction if exists
    reference = transaction.reference
    mydak_transaction = None
    if reference and reference.startswith('ORD-'):
        try:
            trans_id = int(reference.split('-')[1])
            mydak_transaction = Transaction.objects.get(id=trans_id)
        except (ValueError, Transaction.DoesNotExist):
            pass
    
    # Audit log entries
    audit_logs = AdminAuditLog.objects.filter(
        content_type__model='mpestatransaction',
        object_id=transaction_id
    ).order_by('-created_at')[:20]
    
    return render(request, 'admin/mpesa/transaction_detail.html', {
        'transaction': transaction,
        'mydak_transaction': mydak_transaction,
        'audit_logs': audit_logs,
    })


@login_required
@require_admin
@require_http_methods(['GET', 'POST'])
def mpesa_settings_view(request):
    """
    Configure M-PESA settings.
    """
    if request.method == 'GET':
        return render(request, 'admin/mpesa/settings.html', {
            'mpesa_api_key': settings.get('MPESA_API_KEY', 'Not configured'),
            'mpesa_webhook_url': settings.get('MPESA_WEBHOOK_URL', 'Not configured'),
            'mpesa_webhook_verify': settings.get('MPESA_WEBHOOK_VERIFY_SIGNATURE', True),
        })
    
    # POST: Update settings (would require proper admin form handling)
    # For now, just show a message that settings are managed via Django settings
    return render(request, 'admin/mpesa/settings.html', {
        'message': 'M-PESA settings are managed via Django settings.py environment variables',
    })


@login_required
@require_admin
@require_http_methods(['GET'])
def mpesa_analytics_view(request):
    """
    Display M-PESA payment analytics and trends.
    """
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    transactions = MpesaTransaction.objects.filter(created_at__gte=start_date)
    
    # Daily stats
    daily_stats = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        day_trans = transactions.filter(
            created_at__date=date.date()
        )
        daily_stats.append({
            'date': date.date(),
            'count': day_trans.count(),
            'amount': day_trans.aggregate(Sum('amount'))['amount__sum'] or 0,
            'success': day_trans.filter(status='success').count(),
            'failed': day_trans.filter(status='failed').count(),
        })
    
    # Transaction type breakdown
    type_stats = {}
    for trans_type, display in MpesaTransaction._meta.get_field('transaction_type').choices:
        count = transactions.filter(transaction_type=trans_type).count()
        amount = transactions.filter(transaction_type=trans_type).aggregate(
            total=Sum('amount')
        )['total'] or 0
        type_stats[display] = {
            'count': count,
            'amount': amount,
        }
    
    # Phone number usage
    top_phones = transactions.values('phone').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('-count')[:10]
    
    return render(request, 'admin/mpesa/analytics.html', {
        'daily_stats': daily_stats,
        'type_stats': type_stats,
        'top_phones': top_phones,
        'days': days,
    })


@login_required
@require_admin
@require_http_methods(['POST'])
def mpesa_refund_view(request, transaction_id):
    """
    Process admin refund for a transaction.
    
    Note: This requires B2C endpoint which has been removed.
    For now, this is a placeholder for future implementation.
    """
    transaction = get_object_or_404(MpesaTransaction, id=transaction_id)
    
    if transaction.status != 'success':
        return JsonResponse({
            'success': False,
            'error': 'Can only refund successful transactions'
        }, status=400)
    
    # TODO: Implement refund via Reversal endpoint
    # For now, just log the refund request
    refund_amount = request.POST.get('amount', transaction.amount)
    reason = request.POST.get('reason', 'Admin refund')
    
    logger.info(
        f'Refund requested: Transaction {transaction_id}, '
        f'Amount {refund_amount}, Reason: {reason}'
    )
    
    # Create audit log entry
    from app.models import AdminAuditLog
    AdminAuditLog.objects.create(
        admin_user=request.user,
        activity_type='refund_requested',
        description=f'Refund requested for transaction {transaction_id}: {reason}',
        content_type_id=None,
        object_id=transaction_id,
    )
    
    return JsonResponse({
        'success': True,
        'message': 'Refund request submitted. Manual processing required.'
    })
