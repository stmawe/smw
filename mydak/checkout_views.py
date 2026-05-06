"""
Buyer checkout flow with M-PESA payment integration.

Handles:
- Listing/item purchase checkout
- M-PESA STK Push payment initiation
- Payment status tracking
- Order completion workflows
"""

import logging
import json
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction as db_transaction
from django.utils import timezone

from mydak.models import Transaction, Listing, Shop
from app.models import MpesaTransaction
from app.mpesa_gateway import get_mpesa_client, MpesaValidationError, MpesaAPIError

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Extract client IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
@require_http_methods(['GET', 'POST'])
def checkout_view(request, listing_id):
    """
    Buyer checkout for purchasing a listing.
    
    GET: Show checkout form with listing details
    POST: Initiate M-PESA payment
    """
    listing = get_object_or_404(Listing, id=listing_id)
    
    # Can't buy your own listing
    if listing.seller == request.user:
        return redirect('mydak:listing_detail', listing_id=listing_id)
    
    if request.method == 'GET':
        return render(request, 'checkout/checkout.html', {
            'listing': listing,
            'amount': listing.price,
        })
    
    # POST: Initiate payment
    phone = request.POST.get('phone', '').strip()
    
    if not phone:
        return render(request, 'checkout/checkout.html', {
            'listing': listing,
            'amount': listing.price,
            'error': 'Phone number is required',
        }, status=400)
    
    try:
        with db_transaction.atomic():
            # Create Transaction record
            transaction_obj = Transaction.objects.create(
                user=request.user,
                shop=listing.shop,
                listing=listing,
                action='item_purchase',
                amount=Decimal(str(listing.price)),
                status='pending',
                payment_method='mpesa',
                phone_number=phone,
                metadata={
                    'listing_title': listing.title,
                    'listing_id': listing.id,
                    'seller_id': listing.seller.id,
                }
            )
            
            # Initiate M-PESA STK Push
            client = get_mpesa_client()
            reference = f'ORD-{transaction_obj.id}'
            
            response = client.stk_push(
                phone=phone,
                amount=int(listing.price),
                reference=reference,
                description=f'Purchase: {listing.title[:50]}'
            )
            
            # Create MpesaTransaction for tracking
            mpesa_transaction = MpesaTransaction.create_from_stk_push(
                user=request.user,
                phone=phone,
                amount=Decimal(str(listing.price)),
                reference=reference,
                response=response,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Link them together
            transaction_obj.mpesa_checkout_request_id = response.get('CheckoutRequestID')
            transaction_obj.reference_id = reference
            transaction_obj.mark_as_initiated()
            
            # Store link in metadata for easier retrieval
            transaction_obj.metadata['mpesa_transaction_id'] = mpesa_transaction.id
            transaction_obj.save()
            
            logger.info(
                f'Payment initiated: User={request.user.id}, '
                f'Listing={listing.id}, '
                f'Amount={listing.price}, '
                f'CheckoutID={response.get("CheckoutRequestID")}'
            )
            
            return redirect('mydak:checkout_status', transaction_id=transaction_obj.id)
    
    except MpesaValidationError as e:
        logger.warning(f'M-PESA validation error: {str(e)}')
        return render(request, 'checkout/checkout.html', {
            'listing': listing,
            'amount': listing.price,
            'error': f'Invalid phone number: {str(e)}',
        }, status=400)
    
    except MpesaAPIError as e:
        logger.error(f'M-PESA API error: {str(e)}')
        return render(request, 'checkout/checkout.html', {
            'listing': listing,
            'amount': listing.price,
            'error': 'Payment service error. Please try again.',
        }, status=500)
    
    except Exception as e:
        logger.error(f'Checkout error: {str(e)}')
        # Clean up transaction on error
        if transaction_obj.id:
            transaction_obj.delete()
        return render(request, 'checkout/checkout.html', {
            'listing': listing,
            'amount': listing.price,
            'error': 'An error occurred. Please try again.',
        }, status=500)


@login_required
@require_http_methods(['GET'])
def checkout_status_view(request, transaction_id):
    """
    Display payment status and polling UI.
    
    Buyer waits here while M-PESA payment is processed.
    """
    transaction_obj = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    
    return render(request, 'checkout/checkout_status.html', {
        'transaction': transaction_obj,
        'listing': transaction_obj.listing,
        'checkout_request_id': transaction_obj.mpesa_checkout_request_id,
    })


@login_required
@require_http_methods(['GET'])
def checkout_status_poll(request, transaction_id):
    """
    AJAX endpoint to poll payment status.
    
    Returns JSON with current payment status.
    """
    transaction_obj = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    
    if not transaction_obj.mpesa_checkout_request_id:
        return JsonResponse({
            'success': False,
            'error': 'No payment in progress'
        }, status=400)
    
    try:
        # Check MpesaTransaction for latest status
        mpesa_id = transaction_obj.metadata.get('mpesa_transaction_id')
        if mpesa_id:
            mpesa_transaction = MpesaTransaction.objects.get(id=mpesa_id)
            status = mpesa_transaction.status
            receipt = mpesa_transaction.receipt
            
            # Update Transaction status if changed
            if status == 'success' and transaction_obj.status == 'initiated':
                transaction_obj.mpesa_receipt = receipt
                transaction_obj.mark_as_success()
            elif status == 'failed' and transaction_obj.status == 'initiated':
                transaction_obj.mark_as_failed()
        else:
            status = transaction_obj.status
            receipt = transaction_obj.mpesa_receipt
        
        return JsonResponse({
            'success': True,
            'status': status,
            'status_display': dict(Transaction.STATUS_CHOICES).get(status, status),
            'receipt': receipt or None,
            'completed': status in ['success', 'failed'],
        })
    
    except MpesaTransaction.DoesNotExist:
        return JsonResponse({
            'success': True,
            'status': transaction_obj.status,
            'status_display': dict(Transaction.STATUS_CHOICES).get(transaction_obj.status),
            'receipt': transaction_obj.mpesa_receipt or None,
            'completed': transaction_obj.status in ['success', 'failed'],
        })
    
    except Exception as e:
        logger.error(f'Status poll error: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': 'Error checking payment status'
        }, status=500)


@login_required
@require_http_methods(['GET'])
def checkout_success_view(request, transaction_id):
    """
    Display order confirmation after successful payment.
    """
    transaction_obj = get_object_or_404(
        Transaction,
        id=transaction_id,
        user=request.user,
        status='success'
    )
    
    return render(request, 'checkout/checkout_success.html', {
        'transaction': transaction_obj,
        'listing': transaction_obj.listing,
        'receipt': transaction_obj.mpesa_receipt,
    })


@login_required
@require_http_methods(['GET'])
def checkout_failed_view(request, transaction_id):
    """
    Display payment failure message.
    Allows user to retry payment.
    """
    transaction_obj = get_object_or_404(
        Transaction,
        id=transaction_id,
        user=request.user,
        status='failed'
    )
    
    return render(request, 'checkout/checkout_failed.html', {
        'transaction': transaction_obj,
        'listing': transaction_obj.listing,
    })
