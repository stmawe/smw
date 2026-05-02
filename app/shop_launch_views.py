"""Shop launch payment views."""

import json
import logging
import secrets
from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse
from django.utils import timezone
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from mydak.models import Transaction
from mydak.mpesa import MpesaBootstrap

from app.shop_creation_service import ShopCreationService
from app.shop_cache import clear_incomplete_shop

logger = logging.getLogger(__name__)


def _verification_from_email():
    return (
        getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        or getattr(settings, 'EMAIL_HOST_USER', None)
        or 'no-reply@smw.local'
    )


def _send_verification_email(email, code, minutes=10):
    context = {
        'code': code,
        'minutes': minutes,
        'support_email': _verification_from_email(),
    }
    subject = 'Your SMW verification code'
    text_body = render_to_string('emails/shop_email_verification.txt', context)
    html_body = render_to_string('emails/shop_email_verification.html', context)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=_verification_from_email(),
        to=[email],
    )
    message.attach_alternative(html_body, 'text/html')
    message.send(fail_silently=False)


def _is_allowed_verification_email(email):
    email = (email or '').strip().lower()
    return email.endswith('.edu') or email.endswith('.ac.ke')


@login_required
@require_http_methods(['POST'])
def shop_email_verification_send_view(request):
    """Send a one-time verification code to the student's email."""
    email = (request.POST.get('email') or '').strip().lower()
    if not email:
        return JsonResponse({'error': 'Email is required'}, status=400)
    if not _is_allowed_verification_email(email):
        return JsonResponse({'error': 'Use a .edu or .ac.ke email address'}, status=400)

    code = f'{secrets.randbelow(1000000):06d}'
    request.session['shop_email_verification'] = {
        'email': email,
        'code': code,
        'verified': False,
        'expires_at': (timezone.now() + timedelta(minutes=10)).isoformat(),
    }
    request.session.modified = True

    _send_verification_email(email, code)

    response = {'sent': True}
    if settings.DEBUG:
        response['verification_code'] = code
    return JsonResponse(response)


@login_required
@require_http_methods(['POST'])
def shop_email_verification_verify_view(request):
    """Verify a previously sent email code."""
    email = (request.POST.get('email') or '').strip().lower()
    code = (request.POST.get('code') or '').strip()
    payload = request.session.get('shop_email_verification') or {}

    if not email or not code:
        return JsonResponse({'error': 'Email and code are required'}, status=400)
    if payload.get('email') != email:
        return JsonResponse({'error': 'No verification code was sent to this email'}, status=400)

    expires_at = payload.get('expires_at')
    if expires_at and timezone.now() > datetime.fromisoformat(expires_at):
        return JsonResponse({'error': 'Verification code expired'}, status=400)

    if payload.get('code') != code:
        return JsonResponse({'error': 'Invalid verification code'}, status=400)

    payload['verified'] = True
    request.session['shop_email_verification'] = payload
    request.session.modified = True

    return JsonResponse({
        'verified': True,
        'email': email,
        'badge': 'Verified Student',
    })


@login_required
@require_http_methods(['POST'])
def create_shop_api_view(request):
    """Create a draft shop and initiate payment via JSON/POST."""
    payload = ShopCreationService.build_payload(request.POST)

    try:
        shop, transaction, result = ShopCreationService.launch_shop(
            request.user,
            payload,
            request.FILES,
        )
    except ValidationError as exc:
        errors = exc.message_dict if hasattr(exc, 'message_dict') else {'error': exc.messages}
        return JsonResponse({'error': errors}, status=400)

    return JsonResponse({
        'shop_id': shop.id,
        'shop_name': shop.name,
        'transaction_id': transaction.id,
        'checkout_request_id': transaction.mpesa_checkout_request_id,
        'status': transaction.status,
        'payment': result,
    })


@csrf_exempt
@require_http_methods(['POST'])
def shop_mpesa_callback_view(request):
    """Handle the M-Pesa callback for shop launch payments."""
    try:
        callback_data = json.loads(request.body or '{}')
        mpesa = MpesaBootstrap()
        result = mpesa.handle_callback(callback_data)

        checkout_request_id = (
            callback_data.get('Body', {})
            .get('stkCallback', {})
            .get('CheckoutRequestID')
        )

        transaction = Transaction.objects.select_related('shop', 'user').filter(
            mpesa_checkout_request_id=checkout_request_id,
            action='shop_creation',
        ).first()

        if transaction and result.get('success') and transaction.status == 'success':
            ShopCreationService.activate_shop_from_transaction(transaction)
            if transaction.user_id:
                clear_incomplete_shop(transaction.user_id)

        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Received'})
    except Exception as exc:
        logger.error('Shop callback failed: %s', exc)
        return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Error'}, status=500)


@require_http_methods(['GET'])
def shop_payment_status_api(request):
    """Return the current payment status for a launch transaction."""
    ref = (request.GET.get('ref') or '').strip()
    if not ref:
        return JsonResponse({'error': 'ref is required'}, status=400)

    transaction = Transaction.objects.select_related('shop').filter(
        mpesa_checkout_request_id=ref
    ).first()

    if not transaction:
        transaction = Transaction.objects.select_related('shop').filter(
            reference_id=ref
        ).first()

    if not transaction:
        try:
            transaction = Transaction.objects.select_related('shop').get(id=ref)
        except (Transaction.DoesNotExist, ValueError):
            transaction = None

    if not transaction:
        return JsonResponse({'error': 'Transaction not found'}, status=404)

    return JsonResponse({
        'status': transaction.status,
        'transaction_id': transaction.id,
        'checkout_request_id': transaction.mpesa_checkout_request_id,
        'shop_id': transaction.shop_id,
        'shop_active': bool(transaction.shop and transaction.shop.is_active),
        'receipt': transaction.mpesa_receipt,
    })
