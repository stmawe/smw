"""M-Pesa integration module (Bootstrap Implementation)."""

import os
import json
import requests
import logging
from datetime import datetime
from django.conf import settings
from django.utils.timezone import now
from mydak.models import Transaction

logger = logging.getLogger(__name__)

# Fee schedule for bootstrap implementation
FEE_SCHEDULE = {
    'shop_creation': 500,  # KES 500
    'shop_premium': 200,  # KES 200
    'listing_post': 50,  # KES 50
    'listing_feature': 100,  # KES 100 per week
    'item_purchase': 'negotiated',  # Dynamic based on item price
}


class MpesaBootstrap:
    """
    Bootstrap M-Pesa integration using Daraja API.
    In production, this would be fully integrated with M-Pesa callbacks.
    For now, this is a placeholder that tracks payment intents.
    """
    
    def __init__(self):
        self.consumer_key = os.environ.get('MPESA_CONSUMER_KEY', '')
        self.consumer_secret = os.environ.get('MPESA_CONSUMER_SECRET', '')
        self.shortcode = os.environ.get('MPESA_SHORTCODE', '')
        self.passkey = os.environ.get('MPESA_PASSKEY', '')
        self.callback_url = os.environ.get('MPESA_CALLBACK_URL', 'https://example.com/api/mpesa/callback/')
        self.api_url = 'https://sandbox.safaricom.co.ke'  # Sandbox for bootstrap
        self.access_token = None
    
    def get_access_token(self):
        """Get M-Pesa access token (bootstrap: returns dummy token)."""
        if not self.consumer_key or not self.consumer_secret:
            logger.warning('M-Pesa credentials not configured (bootstrap mode)')
            return 'BOOTSTRAP_TOKEN_12345'
        
        try:
            url = f'{self.api_url}/oauth/v1/generate?grant_type=client_credentials'
            response = requests.get(
                url,
                auth=(self.consumer_key, self.consumer_secret),
                timeout=5
            )
            if response.status_code == 200:
                self.access_token = response.json().get('access_token')
                return self.access_token
        except Exception as e:
            logger.error(f'Failed to get M-Pesa token: {e}')
        
        return 'BOOTSTRAP_TOKEN_12345'
    
    def initiate_stk_push(self, phone, amount, transaction_id, description='UniMarket Payment'):
        """
        Initiate M-Pesa STK push (bootstrap: simulates request).
        
        Args:
            phone: Phone number in format 254XXXXXXXXX
            amount: Amount in KES (int)
            transaction_id: UniMarket Transaction ID
            description: Payment description
        
        Returns:
            dict with checkout_request_id or error
        """
        if not phone.startswith('254') or len(phone) != 12:
            return {'error': 'Invalid phone number format'}
        
        try:
            token = self.get_access_token()
            
            # Generate timestamp
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            
            # In bootstrap mode, generate a dummy checkout request ID
            checkout_request_id = f'BOOTSTRAP_{transaction_id}_{timestamp}'
            
            # In production, this would call actual Daraja API
            if self.consumer_key and self.consumer_secret:
                url = f'{self.api_url}/mpesa/stkpush/v1/processrequest'
                headers = {'Authorization': f'Bearer {token}'}
                
                # Generate password (base64 encoded shortcode+passkey+timestamp)
                import base64
                password_str = f'{self.shortcode}{self.passkey}{timestamp}'
                password = base64.b64encode(password_str.encode()).decode()
                
                payload = {
                    'BusinessShortCode': self.shortcode,
                    'Password': password,
                    'Timestamp': timestamp,
                    'TransactionType': 'CustomerPayBillOnline',
                    'Amount': int(amount),
                    'PartyA': phone,
                    'PartyB': self.shortcode,
                    'PhoneNumber': phone,
                    'CallBackURL': self.callback_url,
                    'AccountReference': f'TRX_{transaction_id}',
                    'TransactionDesc': description,
                }
                
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    checkout_request_id = result.get('CheckoutRequestID', checkout_request_id)
                    logger.info(f'STK push initiated: {checkout_request_id}')
                    return {
                        'checkout_request_id': checkout_request_id,
                        'request_id': result.get('RequestId'),
                        'response_code': result.get('ResponseCode'),
                    }
                else:
                    logger.error(f'STK push failed: {response.text}')
                    return {'error': 'Failed to initiate payment'}
            else:
                logger.info(f'STK push (bootstrap): {checkout_request_id} for {phone} ({amount} KES)')
                return {
                    'checkout_request_id': checkout_request_id,
                    'bootstrap': True,
                }
        
        except Exception as e:
            logger.error(f'STK push error: {e}')
            return {'error': str(e)}
    
    def query_payment_status(self, checkout_request_id):
        """Query payment status (bootstrap: checks database)."""
        try:
            transaction = Transaction.objects.filter(
                mpesa_checkout_request_id=checkout_request_id
            ).first()
            
            if transaction:
                return {
                    'status': transaction.status,
                    'amount': str(transaction.amount),
                    'receipt': transaction.mpesa_receipt,
                }
            
            return {'error': 'Transaction not found'}
        
        except Exception as e:
            logger.error(f'Status query error: {e}')
            return {'error': str(e)}
    
    def handle_callback(self, callback_data):
        """
        Handle M-Pesa callback (bootstrap: simulates processing).
        In production, this would be called by M-Pesa after payment.
        """
        try:
            # Extract result code and checkout request ID from callback
            result_code = callback_data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
            checkout_request_id = callback_data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
            
            # Find transaction
            transaction = Transaction.objects.filter(
                mpesa_checkout_request_id=checkout_request_id
            ).first()
            
            if not transaction:
                logger.warning(f'Callback for unknown transaction: {checkout_request_id}')
                return {'error': 'Transaction not found'}
            
            if result_code == 0:  # Success
                # Extract M-Pesa receipt
                callback_metadata = callback_data.get('Body', {}).get('stkCallback', {}).get('CallbackMetadata', {})
                items = {item['Name']: item['Value'] for item in callback_metadata.get('Item', [])}
                
                receipt = items.get('MpesaReceiptNumber', 'BOOTSTRAP_RECEIPT')
                
                transaction.mpesa_receipt = receipt
                transaction.mark_as_success()
                
                logger.info(f'Payment successful: {checkout_request_id} -> {receipt}')
                return {'success': True, 'receipt': receipt}
            
            else:
                transaction.mark_as_failed()
                logger.warning(f'Payment failed: {checkout_request_id} (code: {result_code})')
                return {'error': f'Payment failed with code {result_code}'}
        
        except Exception as e:
            logger.error(f'Callback processing error: {e}')
            return {'error': str(e)}


def get_transaction_amount(action, listing=None, item_price=None):
    """Calculate transaction amount based on action."""
    if action not in FEE_SCHEDULE:
        raise ValueError(f'Unknown action: {action}')
    
    amount = FEE_SCHEDULE[action]
    
    if amount == 'negotiated':
        if item_price:
            return int(item_price * 0.05)  # 5% platform fee
        return 0
    
    return int(amount)
