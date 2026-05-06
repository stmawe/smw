"""
M-PESA Daraja Gateway Integration Module

Custom API wrapper for the Daraja M-PESA Gateway.
Documentation: https://apidj.pgwiz.cloud/docs/

API Key: 0cac939ad63cc94216c73945bec23980
Test Number: 254111791418 / 0111791418
"""

import requests
import json
import logging
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class MpesaGatewayError(Exception):
    """Base exception for M-Pesa gateway errors."""
    pass


class MpesaValidationError(MpesaGatewayError):
    """Raised when request validation fails."""
    pass


class MpesaAPIError(MpesaGatewayError):
    """Raised when API returns an error response."""
    pass


class MpesaClient:
    """
    Client for the Daraja M-PESA Gateway API.
    
    Handles all communication with the custom M-PESA API including:
    - STK Push (Lipa Na M-PESA Online)
    - STK Status polling
    - Reversal (undo payments)
    - Dynamic QR Code generation
    - Transaction status lookup
    - Account Balance
    """
    
    BASE_URL = "https://apidj.pgwiz.cloud/api"
    
    def __init__(self, api_key: str):
        """
        Initialize M-PESA client.
        
        Args:
            api_key: API key from https://apidj.pgwiz.cloud/user/
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-Api-Key': api_key,
        })
    
    def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a POST request to the M-PESA API.
        
        Args:
            endpoint: API endpoint (e.g., 'stk_push', 'stk_status')
            payload: Request payload
            
        Returns:
            Response data dictionary
            
        Raises:
            MpesaAPIError: If API returns an error
            requests.RequestException: On network errors
        """
        # Add .php extension if not already present
        if not endpoint.endswith('.php'):
            endpoint = f"{endpoint}.php"
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            logger.debug(f"M-PESA Request: {url}")
            response = self.session.post(url, json=payload, timeout=10)
            data = response.json()
            
            # Check for error response (ResponseCode != 0 and != 00)
            if data.get('ResponseCode') not in ['0', '00']:
                raise MpesaAPIError(
                    f"API Error {data.get('ResponseCode')}: {data.get('ResponseDescription')}"
                )
            
            logger.info(f"M-PESA Response: {data.get('ResponseDescription')}")
            return data
        
        except requests.RequestException as e:
            logger.error(f"Network error calling M-PESA API: {str(e)}")
            raise
    
    def _make_transaction_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a POST request to the M-PESA API for transaction endpoints.
        
        These endpoints return different response format: {"success": true, "transactions": [...]}
        
        Args:
            endpoint: API endpoint (e.g., 'get_transactions')
            payload: Request payload
            
        Returns:
            Response data dictionary
            
        Raises:
            MpesaAPIError: If API returns an error
            requests.RequestException: On network errors
        """
        # Add .php extension if not already present
        if not endpoint.endswith('.php'):
            endpoint = f"{endpoint}.php"
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            logger.debug(f"M-PESA Transaction Request: {url}")
            response = self.session.post(url, json=payload, timeout=10)
            data = response.json()
            
            # Check for success in different response format
            if not data.get('success'):
                raise MpesaAPIError(
                    f"API Error: Transaction query failed"
                )
            
            logger.info(f"M-PESA Transactions Response: Found {data.get('count', 0)} transactions")
            return data
        
        except requests.RequestException as e:
            logger.error(f"Network error calling M-PESA API: {str(e)}")
            raise
    
    def _normalize_phone(self, phone: str) -> str:
        """
        Normalize phone number to 254XXXXXXXXX format.
        
        Accepts:
        - 254712345678 (already normalized)
        - 0712345678 (Kenya format)
        - 712345678 (9 digits)
        
        Args:
            phone: Phone number in any format
            
        Returns:
            Normalized phone number (254XXXXXXXXX)
            
        Raises:
            MpesaValidationError: If phone is invalid
        """
        phone = str(phone).strip()
        
        # Remove spaces/dashes
        phone = phone.replace(' ', '').replace('-', '')
        
        # Handle leading 0
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        # Handle 9 digits (add 254)
        elif len(phone) == 9 and phone.isdigit():
            phone = '254' + phone
        # Already has 254
        elif not phone.startswith('254'):
            raise MpesaValidationError(f"Invalid phone format: {phone}")
        
        # Validate length
        if len(phone) != 12 or not phone.isdigit():
            raise MpesaValidationError(f"Invalid phone format: {phone}")
        
        return phone
    
    def _validate_amount(self, amount: Any) -> int:
        """
        Validate and convert amount to integer KES.
        
        Args:
            amount: Amount in KES (int, float, Decimal, or string)
            
        Returns:
            Amount as integer
            
        Raises:
            MpesaValidationError: If amount is invalid
        """
        try:
            amt = Decimal(str(amount))
            if amt < 1:
                raise ValueError("Amount must be >= 1")
            return int(amt)
        except (ValueError, TypeError) as e:
            raise MpesaValidationError(f"Invalid amount: {amount}. {str(e)}")
        except Exception as e:
            raise MpesaValidationError(f"Invalid amount: {amount}. {type(e).__name__}: {str(e)}")
    
    # =====================================================================
    # STK Push (Lipa Na M-PESA Online)
    # =====================================================================
    
    def stk_push(
        self,
        phone: str,
        amount: Any,
        reference: str = "Payment",
        description: str = "Payment"
    ) -> Dict[str, Any]:
        """
        Initiate an STK Push (Lipa Na M-PESA Online) prompt.
        
        Triggers a payment prompt on the customer's phone. They enter their
        M-PESA PIN to authorize the payment.
        
        Args:
            phone: Customer phone number (254XXXXXXXXX, 0XXXXXXXXX, or 9 digits)
            amount: Amount in KES (int >= 1)
            reference: Account reference / order ID (displayed on prompt)
            description: Human-readable description
            
        Returns:
            {
                'MerchantRequestID': '29115-34620561-1',
                'CheckoutRequestID': 'ws_CO_191220191020363925',
                'ResponseCode': '0',
                'ResponseDescription': 'Success. Request accepted for processing',
                'statusCheck': {
                    'checkoutRequestId': 'ws_CO_191220191020363925',
                    'endpoint': 'api/stk_status.php',
                    'polling': 'Poll every 3-5 seconds for up to 2 minutes.'
                }
            }
            
        Raises:
            MpesaValidationError: If parameters are invalid
            MpesaAPIError: If API returns an error
        """
        phone = self._normalize_phone(phone)
        amount = self._validate_amount(amount)
        
        payload = {
            'phone': phone,
            'amount': amount,
            'reference': str(reference)[:50],
            'description': str(description)[:100],
        }
        
        logger.info(f"STK Push: {phone}, KES {amount}")
        return self._make_request('stk_push', payload)
    
    # =====================================================================
    # STK Status (Poll payment status)
    # =====================================================================
    
    def stk_status(self, checkout_request_id: str) -> Dict[str, Any]:
        """
        Poll the status of an STK Push transaction.
        
        Use after STK Push to check if customer completed payment. Does NOT
        count against rate limit. Poll every 3-5 seconds for up to 2 minutes.
        
        Args:
            checkout_request_id: CheckoutRequestID from stk_push response
            
        Returns:
            {
                'checkoutRequestId': 'ws_CO_191220191020363925',
                'status': 'success' | 'pending' | 'failed',
                'receipt': 'UC4C38D22C' | null,
                'resultCode': '0' | null,
                'resultDesc': 'The service request is processed successfully.' | null,
                'amount': 100,
                'phone': '254712345678',
                'createdAt': '2026-03-04 14:30:00'
            }
            
        Raises:
            MpesaValidationError: If checkout_request_id is invalid
            MpesaAPIError: If API returns an error or transaction not found
        """
        if not checkout_request_id or not isinstance(checkout_request_id, str):
            raise MpesaValidationError("checkout_request_id must be a non-empty string")
        
        payload = {'checkoutRequestId': checkout_request_id}
        
        logger.debug(f"STK Status: {checkout_request_id}")
        # Use stk_query.php endpoint
        return self._make_request('stk_query', payload)
    
    # =====================================================================
    # Reversal (Undo a transaction)
    # =====================================================================
    
    def reversal(
        self,
        transaction_id: str,
        amount: Any,
        remarks: str = "Reversal",
        occasion: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reverse a completed M-PESA transaction.
        
        Funds are returned to the sender's account. Typically used for
        correcting erroneous payments.
        
        Args:
            transaction_id: M-PESA transaction ID to reverse (e.g., 'OEI2AK4Q16')
            amount: Amount to reverse in KES (int >= 1)
            remarks: Reason for reversal (max 100 chars)
            occasion: Optional occasion for reversal
            
        Returns:
            {
                'ConversationID': 'AG_20191219_00005c92cafb81236f16',
                'OriginatorConversationID': '16740-34861299-1',
                'ResponseCode': '0',
                'ResponseDescription': 'Accept the service request successfully.'
            }
            
        Raises:
            MpesaValidationError: If parameters are invalid
            MpesaAPIError: If API returns an error
        """
        if not transaction_id:
            raise MpesaValidationError("transaction_id is required")
        
        amount = self._validate_amount(amount)
        
        payload = {
            'transactionId': str(transaction_id),
            'amount': amount,
            'remarks': str(remarks)[:100],
        }
        
        if occasion:
            payload['occasion'] = str(occasion)[:50]
        
        logger.warning(f"Reversal: Transaction {transaction_id}, KES {amount}")
        return self._make_request('reversal', payload)
    
    # =====================================================================
    # QR Code Generation
    # =====================================================================
    
    def qr_code(
        self,
        amount: Any,
        merchant_name: Optional[str] = None,
        reference: Optional[str] = None,
        transaction_type: str = "BG"
    ) -> Dict[str, Any]:
        """
        Generate a dynamic M-PESA QR code.
        
        Customer scans the code with M-PESA app to complete payment.
        Useful for in-store and point-of-sale scenarios.
        
        Args:
            amount: Amount in KES (int >= 1)
            merchant_name: Name of merchant displayed on QR code
            reference: Payment reference or order number
            transaction_type: QR transaction type code (default: "BG" - Buy Goods)
            
        Returns:
            {
                'ResponseCode': '0',
                'RequestID': 'QR-1001',
                'ResponseDescription': 'QR code generated successfully.',
                'QRCode': 'data:image/png;base64,iVBOR...'  # Base64 PNG image
            }
            
        Raises:
            MpesaValidationError: If parameters are invalid
            MpesaAPIError: If API returns an error
        """
        amount = self._validate_amount(amount)
        
        payload = {
            'amount': amount,
            'transactionType': transaction_type,
        }
        
        if merchant_name:
            payload['merchantName'] = str(merchant_name)[:50]
        if reference:
            payload['reference'] = str(reference)[:50]
        
        logger.info(f"QR Code: KES {amount}")
        return self._make_request('qr_code', payload)
    
    # =====================================================================
    # Transaction Status Lookup
    # =====================================================================
    
    def transaction_status(self, transaction_id: str) -> Dict[str, Any]:
        """
        Query the status of any M-PESA transaction by ID.
        
        Use to verify whether a payment was completed, failed, or is pending.
        
        Args:
            transaction_id: M-PESA transaction ID (e.g., 'OEI2AK4Q16')
            
        Returns:
            {
                'ResponseCode': '0',
                'ResponseDescription': 'Accept the service request successfully.',
                'ConversationID': 'AG_20191219_00005e83b2effadd5b6a',
                'OriginatorConversationID': '16740-34861444-1'
            }
            
        Raises:
            MpesaValidationError: If transaction_id is invalid
            MpesaAPIError: If API returns an error
        """
        if not transaction_id:
            raise MpesaValidationError("transaction_id is required")
        
        payload = {'transactionId': str(transaction_id)}
        
        logger.info(f"Transaction Status: {transaction_id}")
        # Use get_transactions.php endpoint which returns different format
        return self._make_transaction_request('get_transactions', payload)


class MpesaTransaction:
    """
    Database model representation for M-PESA transactions.
    
    Tracks all M-PESA payments in the system:
    - STK Push initiations
    - Payment completions
    - B2C disbursements
    - Reversals
    """
    
    # Transaction types
    TYPE_STK_PUSH = 'stk_push'
    TYPE_STK_STATUS = 'stk_status'
    TYPE_B2C = 'b2c'
    TYPE_REVERSAL = 'reversal'
    
    # Status values
    STATUS_PENDING = 'pending'
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'
    
    @staticmethod
    def create_from_stk_push(
        user_id: int,
        phone: str,
        amount: int,
        reference: str,
        merchant_request_id: str,
        checkout_request_id: str
    ) -> 'MpesaTransaction':
        """
        Create a new transaction record from STK Push response.
        
        Args:
            user_id: User initiating the payment
            phone: Customer phone number
            amount: Amount in KES
            reference: Transaction reference
            merchant_request_id: From M-PESA API response
            checkout_request_id: From M-PESA API response (used for polling)
            
        Returns:
            MpesaTransaction instance
        """
        # TODO: Implement database save
        pass


# =====================================================================
# Django Integration Helpers
# =====================================================================

def get_mpesa_client():
    """Get configured M-PESA client from Django settings."""
    from django.conf import settings
    
    api_key = getattr(settings, 'MPESA_API_KEY', None)
    if not api_key:
        raise MpesaGatewayError(
            "MPESA_API_KEY not configured in Django settings"
        )
    
    return MpesaClient(api_key)


def initialize_mpesa_transaction(
    user_id: int,
    phone: str,
    amount: int,
    reference: str,
    description: str = "Payment"
) -> Tuple[str, str]:
    """
    Initialize an M-PESA STK Push transaction.
    
    Args:
        user_id: User ID initiating payment
        phone: Customer phone number
        amount: Amount in KES
        reference: Order/transaction reference
        description: Payment description
        
    Returns:
        Tuple of (checkout_request_id, merchant_request_id)
        
    Raises:
        MpesaValidationError: If parameters are invalid
        MpesaAPIError: If API call fails
    """
    client = get_mpesa_client()
    
    response = client.stk_push(
        phone=phone,
        amount=amount,
        reference=reference,
        description=description
    )
    
    # TODO: Save transaction record to database
    
    return (
        response.get('CheckoutRequestID'),
        response.get('MerchantRequestID')
    )


def poll_mpesa_transaction_status(checkout_request_id: str) -> Dict[str, Any]:
    """
    Poll the current status of an M-PESA transaction.
    
    Args:
        checkout_request_id: Checkout request ID from initiate_transaction
        
    Returns:
        Transaction status response
        
    Raises:
        MpesaAPIError: If API call fails
    """
    client = get_mpesa_client()
    
    status = client.stk_status(checkout_request_id)
    
    # TODO: Update transaction record in database
    
    return status
