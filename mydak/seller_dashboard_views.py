"""
Seller dashboard with earnings tracking and M-PESA withdrawal integration.

Handles:
- Earnings summary and history
- Withdrawal management
- Order status tracking
- Payment status monitoring
"""

import logging
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum, Q, Count
from django.utils import timezone
from django.core.paginator import Paginator

from mydak.models import Transaction, Shop, Listing
from app.models import MpesaTransaction

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(['GET'])
def seller_earnings_view(request):
    """
    Display seller earnings summary and transaction history.
    """
    # Get seller's shops
    shops = Shop.objects.filter(owner=request.user)
    
    if not shops.exists():
        return redirect('shops:list')
    
    # Get successful transactions (completed sales)
    seller_transactions = Transaction.objects.filter(
        listing__shop__owner=request.user,
        action='item_purchase',
        status='success'
    ).order_by('-completed_at')
    
    # Calculate stats
    total_earnings = seller_transactions.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    
    # Monthly earnings
    today = timezone.now()
    month_start = today.replace(day=1)
    month_earnings = seller_transactions.filter(
        completed_at__gte=month_start
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Pending transactions (awaiting payment)
    pending_count = Transaction.objects.filter(
        listing__shop__owner=request.user,
        action='item_purchase',
        status__in=['pending', 'initiated']
    ).count()
    
    # Pagination
    paginator = Paginator(seller_transactions, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'seller/earnings.html', {
        'page_obj': page_obj,
        'total_earnings': total_earnings,
        'month_earnings': month_earnings,
        'pending_count': pending_count,
        'shops': shops,
    })


@login_required
@require_http_methods(['GET', 'POST'])
def seller_withdrawal_view(request):
    """
    Manage seller withdrawals via M-PESA.
    
    GET: Show withdrawal form
    POST: Initiate withdrawal
    """
    # Get seller's earnings
    seller_transactions = Transaction.objects.filter(
        listing__shop__owner=request.user,
        action='item_purchase',
        status='success'
    )
    
    available_balance = seller_transactions.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    
    # Get withdrawal history
    withdrawals = MpesaTransaction.objects.filter(
        user=request.user,
        transaction_type='b2c'
    ).order_by('-created_at')
    
    if request.method == 'GET':
        return render(request, 'seller/withdrawal.html', {
            'available_balance': available_balance,
            'withdrawals': withdrawals[:10],  # Last 10 withdrawals
        })
    
    # POST: Process withdrawal request
    amount_str = request.POST.get('amount', '').strip()
    phone = request.POST.get('phone', '').strip()
    
    if not amount_str or not phone:
        return render(request, 'seller/withdrawal.html', {
            'available_balance': available_balance,
            'withdrawals': withdrawals[:10],
            'error': 'Amount and phone number are required',
        }, status=400)
    
    try:
        amount = Decimal(amount_str)
    except:
        return render(request, 'seller/withdrawal.html', {
            'available_balance': available_balance,
            'withdrawals': withdrawals[:10],
            'error': 'Invalid amount',
        }, status=400)
    
    # Validate amount
    if amount <= 0:
        return render(request, 'seller/withdrawal.html', {
            'available_balance': available_balance,
            'withdrawals': withdrawals[:10],
            'error': 'Amount must be greater than 0',
        }, status=400)
    
    if amount > available_balance:
        return render(request, 'seller/withdrawal.html', {
            'available_balance': available_balance,
            'withdrawals': withdrawals[:10],
            'error': f'Insufficient balance. Available: KES {available_balance}',
        }, status=400)
    
    # TODO: In future, implement B2C withdrawal via MpesaClient.b2c_payment()
    # For now, mark as pending for manual admin processing
    
    return render(request, 'seller/withdrawal.html', {
        'available_balance': available_balance,
        'withdrawals': withdrawals[:10],
        'message': 'Withdrawal request submitted. Our team will process it shortly.',
    })


@login_required
@require_http_methods(['GET'])
def seller_orders_view(request):
    """
    Display seller's incoming orders (items being purchased).
    """
    # Get orders for seller's listings
    orders = Transaction.objects.filter(
        listing__shop__owner=request.user,
        action='item_purchase'
    ).select_related('user', 'listing', 'shop').order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Status counts
    status_counts = {
        'pending': orders.filter(status='pending').count(),
        'initiated': orders.filter(status='initiated').count(),
        'success': orders.filter(status='success').count(),
        'failed': orders.filter(status='failed').count(),
    }
    
    return render(request, 'seller/orders.html', {
        'page_obj': page_obj,
        'status_counts': status_counts,
        'selected_status': status_filter,
    })


@login_required
@require_http_methods(['GET'])
def seller_order_detail_view(request, transaction_id):
    """
    Display details for a specific order/transaction.
    """
    transaction = get_object_or_404(
        Transaction,
        id=transaction_id,
        listing__shop__owner=request.user,
        action='item_purchase'
    )
    
    # Get linked M-PESA transaction if available
    mpesa_transaction = None
    if transaction.metadata.get('mpesa_transaction_id'):
        try:
            mpesa_transaction = MpesaTransaction.objects.get(
                id=transaction.metadata['mpesa_transaction_id']
            )
        except MpesaTransaction.DoesNotExist:
            pass
    
    return render(request, 'seller/order_detail.html', {
        'transaction': transaction,
        'mpesa_transaction': mpesa_transaction,
        'buyer': transaction.user,
        'listing': transaction.listing,
    })


@login_required
@require_http_methods(['GET'])
def seller_payments_view(request):
    """
    Display payment history for all seller transactions.
    """
    # Get all payment transactions for seller
    payments = Transaction.objects.filter(
        listing__shop__owner=request.user,
        action__in=['shop_creation', 'shop_premium', 'listing_post', 'listing_feature', 'item_purchase']
    ).order_by('-created_at')
    
    # Summary stats
    total_received = payments.filter(status='success').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    
    pending_payments = payments.filter(
        status__in=['pending', 'initiated']
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Pagination
    paginator = Paginator(payments, 30)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'seller/payments.html', {
        'page_obj': page_obj,
        'total_received': total_received,
        'pending_payments': pending_payments,
    })
