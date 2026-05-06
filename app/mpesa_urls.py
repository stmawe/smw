"""
M-PESA Payment API URL Patterns

Endpoints:
  POST   /api/mpesa/webhook/              - M-PESA callback handler
  POST   /api/mpesa/pay/                  - Initiate STK Push payment
  GET    /api/mpesa/status/<checkout_id>/ - Poll payment status
  GET    /payments/history/               - View payment history
  GET    /payments/receipt/<id>/          - View payment receipt
  Admin:
  GET    /admin/mpesa/dashboard/          - Admin dashboard
  GET    /admin/mpesa/transactions/       - Transaction list
  GET    /admin/mpesa/settings/           - Settings panel
"""

from django.urls import path
from app.mpesa_payments_views import (
    mpesa_webhook_handler,
    initiate_stk_payment,
    get_payment_status,
    payment_history,
    payment_receipt,
)
from app.mpesa_admin_views import (
    mpesa_dashboard_view,
    mpesa_transactions_view,
    mpesa_transaction_detail_view,
    mpesa_settings_view,
    mpesa_analytics_view,
    mpesa_refund_view,
)

app_name = 'mpesa_payments'

urlpatterns = [
    # Webhook - M-PESA callbacks (no auth required)
    path('api/mpesa/webhook/', mpesa_webhook_handler, name='webhook'),
    
    # Payment APIs
    path('api/mpesa/pay/', initiate_stk_payment, name='initiate_payment'),
    path('api/mpesa/status/<str:checkout_request_id>/', get_payment_status, name='payment_status'),
    
    # Payment pages
    path('payments/history/', payment_history, name='payment_history'),
    path('payments/receipt/<int:transaction_id>/', payment_receipt, name='payment_receipt'),
    
    # Admin dashboard and settings
    path('admin/mpesa/dashboard/', mpesa_dashboard_view, name='admin_dashboard'),
    path('admin/mpesa/transactions/', mpesa_transactions_view, name='admin_transactions'),
    path('admin/mpesa/transactions/<int:transaction_id>/', mpesa_transaction_detail_view, name='admin_transaction_detail'),
    path('admin/mpesa/settings/', mpesa_settings_view, name='admin_settings'),
    path('admin/mpesa/analytics/', mpesa_analytics_view, name='admin_analytics'),
    path('admin/mpesa/refund/<int:transaction_id>/', mpesa_refund_view, name='admin_refund'),
]
