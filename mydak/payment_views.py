"""Payment views for M-Pesa bootstrap implementation."""

import logging
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from mydak.models import Transaction, Shop, Listing
from mydak.payment_forms import PaymentInitiateForm
from mydak.mpesa import MpesaBootstrap, get_transaction_amount

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(['GET', 'POST'])
def payment_initiate_view(request, transaction_id=None):
    """
    Initiate payment for a transaction or create a new one.
    
    GET: Show payment form
    POST: Process payment initiation
    """
    if transaction_id:
        # Existing transaction
        transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
        if transaction.status != 'pending':
            return redirect('payment_status', transaction_id=transaction_id)
    else:
        return redirect('shops:list')  # Must have a transaction already
    
    if request.method == 'GET':
        form = PaymentInitiateForm()
        return render(request, 'payments/payment_initiate.html', {
            'form': form,
            'transaction': transaction,
            'amount': transaction.amount,
        })
    
    # POST: Process payment
    form = PaymentInitiateForm(request.POST)
    if not form.is_valid():
        return render(request, 'payments/payment_initiate.html', {
            'form': form,
            'transaction': transaction,
            'error': 'Invalid form data'
        }, status=400)
    
    phone = form.cleaned_data['phone_number']
    
    # Initiate M-Pesa STK push
    mpesa = MpesaBootstrap()
    result = mpesa.initiate_stk_push(
        phone=phone,
        amount=int(transaction.amount),
        transaction_id=transaction.id,
        description=f'{transaction.get_action_display()} - UniMarket'
    )
    
    if 'error' in result:
        return render(request, 'payments/payment_initiate.html', {
            'form': form,
            'transaction': transaction,
            'error': result['error']
        }, status=400)
    
    # Update transaction with checkout request ID
    transaction.phone_number = phone
    transaction.mpesa_checkout_request_id = result.get('checkout_request_id')
    transaction.mark_as_initiated()
    
    # Redirect to status check
    return redirect('payment_status', transaction_id=transaction.id)


@login_required
@require_http_methods(['GET'])
def payment_status_view(request, transaction_id):
    """Check and display payment status."""
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    
    # Optionally query M-Pesa for latest status
    if transaction.status == 'initiated' and transaction.mpesa_checkout_request_id:
        mpesa = MpesaBootstrap()
        status_result = mpesa.query_payment_status(transaction.mpesa_checkout_request_id)
        
        if 'status' in status_result:
            transaction.status = status_result['status']
            transaction.save()
    
    return render(request, 'payments/payment_status.html', {
        'transaction': transaction,
        'status_display': transaction.get_status_display(),
    })


@login_required
@require_http_methods(['POST'])
def payment_action_view(request, action):
    """
    Create a transaction for a specific action and initiate payment.
    
    Actions: shop_creation, listing_post, listing_feature, etc.
    """
    if action not in [choice[0] for choice in Transaction.ACTION_CHOICES]:
        return JsonResponse({'error': 'Invalid action'}, status=400)
    
    try:
        amount = get_transaction_amount(action)
        
        # Create transaction
        transaction = Transaction.objects.create(
            user=request.user,
            action=action,
            amount=amount,
            status='pending',
            payment_method='mpesa'
        )
        
        # Redirect to payment form
        return redirect('payment_initiate', transaction_id=transaction.id)
    
    except Exception as e:
        logger.error(f'Failed to create transaction: {e}')
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(['POST'])
def mpesa_callback_view(request):
    """
    Handle M-Pesa callback (webhook).
    This is called by M-Pesa after user completes/cancels payment.
    """
    try:
        callback_data = json.loads(request.body)
        
        mpesa = MpesaBootstrap()
        result = mpesa.handle_callback(callback_data)
        
        if 'success' in result:
            return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Received'})
        else:
            return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Error'})
    
    except Exception as e:
        logger.error(f'Callback error: {e}')
        return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Error'}, status=500)


@csrf_exempt
@require_http_methods(['POST'])
def mpesa_timeout_view(request):
    """Handle M-Pesa timeout (when user cancels STK push)."""
    try:
        callback_data = json.loads(request.body)
        
        # Mark transaction as failed/expired
        checkout_request_id = callback_data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
        transaction = Transaction.objects.filter(
            mpesa_checkout_request_id=checkout_request_id
        ).first()
        
        if transaction:
            transaction.status = 'expired'
            transaction.save()
            logger.info(f'Payment expired: {checkout_request_id}')
        
        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Received'})
    
    except Exception as e:
        logger.error(f'Timeout callback error: {e}')
        return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Error'}, status=500)
