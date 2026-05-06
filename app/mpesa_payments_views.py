"""
M-PESA Webhook Handler and Payment Views

Handles:
1. M-PESA STK Push callbacks (payment completion notifications)
2. B2C payment callbacks (disbursement confirmations)
3. Payment status polling AJAX endpoints
4. Payment history and receipts
"""

import json
import logging
import hashlib
import hmac
from datetime import datetime, timedelta
from decimal import Decimal

from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
from django.conf import settings

from app.models import MpesaTransaction, User
from app.mpesa_gateway import get_mpesa_client, MpesaGatewayError, MpesaAPIError, MpesaValidationError

logger = logging.getLogger(__name__)


# =====================================================================
# WEBHOOK HANDLER - Receive M-PESA Callbacks
# =====================================================================

@csrf_exempt  # M-PESA callbacks don't include CSRF token
@require_http_methods(["POST"])
def mpesa_webhook_handler(request):
    """
    Handle M-PESA payment result callbacks.
    
    M-PESA sends callback notifications when:
    - STK Push payment completes/fails
    - B2C disbursement completes
    - Transaction status changes
    
    Expected payload (from M-PESA):
    {
        "Body": {
            "stkCallback": {
                "MerchantRequestID": "29115-34620561-1",
                "CheckoutRequestID": "ws_CO_191220191020363925",
                "ResultCode": 0,
                "ResultDesc": "The service request is processed successfully.",
                "CallbackMetadata": {
                    "Item": [
                        {
                            "Name": "Amount",
                            "Value": 100
                        },
                        {
                            "Name": "MpesaReceiptNumber",
                            "Value": "UC4C38D22C"
                        },
                        {
                            "Name": "TransactionDate",
                            "Value": 20260302144001
                        },
                        {
                            "Name": "PhoneNumber",
                            "Value": 254712345678
                        }
                    ]
                }
            }
        }
    }
    """
    
    try:
        # Parse request body
        body = request.body.decode('utf-8')
        logger.debug(f"M-PESA Webhook received: {body[:500]}")
        
        if not body:
            logger.warning("Empty webhook payload")
            return JsonResponse({'success': False, 'error': 'Empty payload'}, status=400)
        
        payload = json.loads(body)
        
        # Verify webhook signature (if configured)
        if getattr(settings, 'MPESA_WEBHOOK_VERIFY_SIGNATURE', True):
            if not verify_webhook_signature(request, payload):
                logger.warning(f"Invalid webhook signature from {request.META.get('REMOTE_ADDR')}")
                return JsonResponse({'success': False, 'error': 'Invalid signature'}, status=403)
        
        # Process the callback
        result = process_mpesa_callback(payload, request)
        
        # Always return 200 to M-PESA (so it knows we received it)
        return JsonResponse(result)
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in webhook: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    
    except Exception as e:
        logger.error(f"Webhook processing error: {type(e).__name__}: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': 'Processing error'}, status=500)


def verify_webhook_signature(request, payload):
    """
    Verify webhook signature from M-PESA.
    
    Uses HMAC-SHA256 with webhook secret.
    
    Args:
        request: Django request object
        payload: Parsed JSON payload
        
    Returns:
        Boolean - True if signature valid
    """
    webhook_secret = getattr(settings, 'MPESA_WEBHOOK_SECRET', None)
    if not webhook_secret:
        logger.warning("MPESA_WEBHOOK_SECRET not configured")
        return False
    
    # Get signature from header
    signature = request.META.get('HTTP_X_SIGNATURE', '')
    if not signature:
        logger.warning("No X-Signature header in webhook")
        return False
    
    # Compute expected signature
    payload_str = json.dumps(payload, sort_keys=True)
    expected_sig = hmac.new(
        webhook_secret.encode(),
        payload_str.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures
    return hmac.compare_digest(signature, expected_sig)


def process_mpesa_callback(payload, request):
    """
    Process M-PESA callback payload.
    
    Handles both STK Push and B2C callbacks.
    
    Args:
        payload: Parsed callback JSON
        request: Django request object
        
    Returns:
        Dict with processing result
    """
    
    try:
        # Extract callback data
        body = payload.get('Body', {})
        stk_callback = body.get('stkCallback', {})
        
        if not stk_callback:
            logger.warning(f"No stkCallback in payload")
            return {'success': False, 'error': 'No callback data'}
        
        # Extract key fields
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        merchant_request_id = stk_callback.get('MerchantRequestID')
        result_code = stk_callback.get('ResultCode')
        result_desc = stk_callback.get('ResultDesc', '')
        
        if not checkout_request_id:
            logger.warning("No CheckoutRequestID in callback")
            return {'success': False, 'error': 'Missing CheckoutRequestID'}
        
        # Find the transaction
        try:
            transaction = MpesaTransaction.objects.get(
                checkout_request_id=checkout_request_id
            )
        except MpesaTransaction.DoesNotExist:
            logger.warning(f"Transaction not found for {checkout_request_id}")
            return {'success': False, 'error': 'Transaction not found'}
        
        # Determine status
        if result_code == 0:
            status = 'success'
        else:
            status = 'failed'
        
        # Extract callback metadata
        callback_metadata = stk_callback.get('CallbackMetadata', {})
        items = {item['Name']: item['Value'] for item in callback_metadata.get('Item', [])}
        
        # Update transaction
        transaction.status = status
        transaction.result_code = str(result_code)
        transaction.result_description = result_desc
        transaction.receipt = items.get('MpesaReceiptNumber', '')
        transaction.response_payload = payload
        transaction.ip_address = get_client_ip(request)
        transaction.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        # Parse transaction date if available
        trans_date_str = items.get('TransactionDate')
        if trans_date_str:
            try:
                # Format: YYYYMMDDHHmmss
                trans_date = datetime.strptime(str(trans_date_str), '%Y%m%d%H%M%S')
                transaction.completed_at = timezone.make_aware(trans_date)
            except (ValueError, TypeError):
                pass
        
        transaction.save()
        
        # Log audit trail
        log_transaction_audit(
            transaction=transaction,
            action='payment_callback',
            description=f'Payment callback received: {status.upper()}',
            result_code=result_code,
            result_description=result_desc
        )
        
        # Post-processing based on status
        if status == 'success':
            handle_payment_success(transaction)
        else:
            handle_payment_failure(transaction)
        
        logger.info(f"Transaction {checkout_request_id} updated: {status}")
        
        return {'success': True, 'message': 'Callback processed'}
        
    except Exception as e:
        logger.error(f"Error processing callback: {type(e).__name__}: {str(e)}", exc_info=True)
        return {'success': False, 'error': str(e)}


def handle_payment_success(transaction):
    """
    Handle successful payment.
    
    Updates order, sends notifications, triggers fulfillment.
    
    Args:
        transaction: MpesaTransaction instance
    """
    try:
        from mydak.models import Transaction as DakTransaction
        
        # Find linked mydak Transaction
        reference = transaction.reference
        if reference and reference.startswith('ORD-'):
            try:
                transaction_id = int(reference.split('-')[1])
                mydak_transaction = DakTransaction.objects.get(id=transaction_id)
                
                # Update mydak transaction
                mydak_transaction.mpesa_receipt = transaction.receipt
                mydak_transaction.mark_as_success()
                
                logger.info(f"Linked mydak transaction {transaction_id} marked as success")
            except (ValueError, DakTransaction.DoesNotExist) as e:
                logger.warning(f"Could not link mydak transaction for {reference}: {e}")
        
        # TODO: Send success email to customer
        # TODO: Send notification to seller
        # TODO: Trigger fulfillment workflow
        
        logger.info(f"Payment success handled for transaction {transaction.id}")
        
    except Exception as e:
        logger.error(f"Error handling payment success: {str(e)}", exc_info=True)


def handle_payment_failure(transaction):
    """
    Handle failed payment.
    
    Sends failure notification, logs reason.
    
    Args:
        transaction: MpesaTransaction instance
    """
    try:
        from mydak.models import Transaction as DakTransaction
        
        # Find linked mydak Transaction
        reference = transaction.reference
        if reference and reference.startswith('ORD-'):
            try:
                transaction_id = int(reference.split('-')[1])
                mydak_transaction = DakTransaction.objects.get(id=transaction_id)
                
                # Update mydak transaction
                mydak_transaction.mark_as_failed()
                
                logger.info(f"Linked mydak transaction {transaction_id} marked as failed")
            except (ValueError, DakTransaction.DoesNotExist) as e:
                logger.warning(f"Could not link mydak transaction for {reference}: {e}")
        
        # TODO: Send failure email to customer
        # TODO: Release any reserved inventory
        # TODO: Log failure reason for investigation
        
        logger.warning(f"Payment failed for transaction {transaction.id}: {transaction.result_description}")
        
    except Exception as e:
        logger.error(f"Error handling payment failure: {str(e)}", exc_info=True)


def log_transaction_audit(transaction, action, description, result_code=None, result_description=None):
    """
    Log transaction audit trail.
    
    Args:
        transaction: MpesaTransaction instance
        action: Action type (e.g., 'payment_callback')
        description: Human-readable description
        result_code: M-PESA result code
        result_description: M-PESA result description
    """
    try:
        from app.models import AdminAuditLog
        
        AdminAuditLog.objects.create(
            admin_user=transaction.user,
            admin_username=transaction.user.username if transaction.user else 'system',
            action='other',
            action_label=f'[MPESA] {description}',
            content_type='MpesaTransaction',
            object_id=str(transaction.id),
            object_str=str(transaction),
            reason=f"Result: {result_description}",
            status='success' if transaction.status == 'success' else 'error',
        )
    except Exception as e:
        logger.error(f"Error logging audit trail: {str(e)}")


def get_client_ip(request):
    """Extract client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# =====================================================================
# PAYMENT VIEWS - Ajax Endpoints and Pages
# =====================================================================

@login_required
@require_http_methods(["POST"])
def initiate_stk_payment(request):
    """
    Initiate STK Push payment for a buyer.
    
    Request:
    {
        'phone': '254712345678',
        'amount': 1000,
        'reference': 'ORD-12345',
        'description': 'Payment for order #12345'
    }
    
    Response:
    {
        'success': true,
        'checkout_request_id': 'ws_CO_...',
        'message': 'Check your phone for M-PESA prompt',
        'polling_url': '/api/mpesa/status/ws_CO_../'
    }
    """
    try:
        data = json.loads(request.body)
        
        phone = data.get('phone', '').strip()
        amount = data.get('amount')
        reference = data.get('reference', f'ORDER-{request.user.id}')
        description = data.get('description', 'Payment')
        
        # Validate input
        if not phone or not amount:
            return JsonResponse({
                'success': False,
                'error': 'Phone and amount are required'
            }, status=400)
        
        # Initialize payment with M-PESA
        client = get_mpesa_client()
        response = client.stk_push(
            phone=phone,
            amount=amount,
            reference=reference,
            description=description
        )
        
        # Save transaction record
        transaction = MpesaTransaction.create_from_stk_push(
            user=request.user,
            phone=phone,
            amount=amount,
            reference=reference,
            response=response,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
        )
        
        logger.info(f"STK Push initiated: {transaction.checkout_request_id}")
        
        return JsonResponse({
            'success': True,
            'checkout_request_id': transaction.checkout_request_id,
            'merchant_request_id': transaction.merchant_request_id,
            'message': f'M-PESA prompt sent to {phone}',
            'polling_url': f'/api/mpesa/status/{transaction.checkout_request_id}/',
        })
        
    except MpesaValidationError as e:
        logger.warning(f"Payment initiation validation error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Invalid input: {str(e)}'
        }, status=400)
    
    except MpesaAPIError as e:
        logger.error(f"M-PESA API error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Payment service temporarily unavailable'
        }, status=502)
    
    except Exception as e:
        logger.error(f"Unexpected error: {type(e).__name__}: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_payment_status(request, checkout_request_id):
    """
    Poll current payment status.
    
    Response:
    {
        'success': true,
        'status': 'pending|success|failed',
        'receipt': 'UC4C38D22C' (if success),
        'message': 'Payment completed successfully',
        'amount': 1000
    }
    """
    try:
        # Get transaction
        transaction = get_object_or_404(
            MpesaTransaction,
            checkout_request_id=checkout_request_id,
            user=request.user
        )
        
        # If status is pending, poll M-PESA
        if transaction.status == 'pending':
            try:
                client = get_mpesa_client()
                status = client.stk_status(checkout_request_id)
                transaction.update_from_status(status)
            except MpesaAPIError:
                # API error - return current status
                pass
            except Exception as e:
                logger.error(f"Error polling status: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'status': transaction.status,
            'receipt': transaction.receipt,
            'amount': float(transaction.amount),
            'phone': transaction.phone,
            'reference': transaction.reference,
            'message': {
                'pending': 'Waiting for M-PESA confirmation...',
                'success': 'Payment completed successfully!',
                'failed': f'Payment failed: {transaction.result_description}'
            }.get(transaction.status, 'Unknown status'),
        })
        
    except Exception as e:
        logger.error(f"Error getting payment status: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error retrieving payment status'
        }, status=500)


# =====================================================================
# PAYMENT HISTORY AND RECEIPTS
# =====================================================================

@login_required
def payment_history(request):
    """
    Display user's M-PESA payment history.
    """
    transactions = MpesaTransaction.objects.filter(
        user=request.user
    ).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Summary stats
    total = transactions.aggregate(Sum('amount'))['amount__sum'] or 0
    successful = transactions.filter(status='success').count()
    
    return render(request, 'mpesa/payment_history.html', {
        'page_obj': page_obj,
        'total_amount': total,
        'successful_count': successful,
    })


@login_required
def payment_receipt(request, transaction_id):
    """
    Display receipt for a specific M-PESA transaction.
    """
    transaction = get_object_or_404(
        MpesaTransaction,
        id=transaction_id,
        user=request.user
    )
    
    return render(request, 'mpesa/payment_receipt.html', {
        'transaction': transaction,
    })

