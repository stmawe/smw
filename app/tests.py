import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from mydak.models import Shop, Transaction
from app.shop_urls import generate_shop_slug, validate_shop_slug


User = get_user_model()


class ShopSlugTests(TestCase):
    def test_generate_shop_slug_normalizes_special_characters(self):
        self.assertEqual(generate_shop_slug("Juju's Electronics!!"), 'jujus-electronics')
        self.assertEqual(generate_shop_slug('  My Cool Shop  '), 'my-cool-shop')
        self.assertEqual(generate_shop_slug('Books & More!!'), 'books-more')

    def test_validate_shop_slug_reports_taken_and_reserved_values(self):
        Shop.objects.create(owner=self.user, name='Juju Electronics', domain='juju-electronics')

        taken = validate_shop_slug('juju-electronics')
        reserved = validate_shop_slug('admin')

        self.assertFalse(taken['available'])
        self.assertFalse(taken['valid'])
        self.assertIn('suggestion', taken)
        self.assertFalse(reserved['available'])
        self.assertFalse(reserved['valid'])

    def setUp(self):
        self.user = User.objects.create_user(
            username='shoptester',
            email='shoptester@example.com',
            password='testpass123',
        )


class ShopLaunchFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='launchuser',
            email='launchuser@example.com',
            password='testpass123',
        )
        self.client.force_login(self.user)

    @patch('app.shop_creation_service.MpesaBootstrap.initiate_stk_push')
    def test_create_shop_api_initiates_payment(self, mock_stk):
        mock_stk.return_value = {'checkout_request_id': 'BOOTSTRAP_1001'}

        response = self.client.post(
            reverse('create_shop_api'),
            {
                'shop_name': 'Launch Shop',
                'description': 'A carefully written description for the launch flow.',
                'category': 'Electronics',
                'location': 'Nairobi',
                'theme_id': 'dark_noir',
                'whatsapp': '0712345678',
                'payment_phone': '0712345678',
                'terms': 'on',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['checkout_request_id'], 'BOOTSTRAP_1001')
        self.assertEqual(Shop.objects.count(), 1)
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(Transaction.objects.first().status, 'initiated')

    def test_payment_status_api_returns_transaction_status(self):
        shop = Shop.objects.create(owner=self.user, name='Pending Shop', domain='pending-shop')
        transaction = Transaction.objects.create(
            user=self.user,
            shop=shop,
            action='shop_creation',
            amount=500,
            status='initiated',
            payment_method='mpesa',
            phone_number='254712345678',
            reference_id='SHOP-1-REF',
            mpesa_checkout_request_id='BOOTSTRAP_1',
        )

        response = self.client.get(reverse('shop_payment_status'), {'ref': transaction.mpesa_checkout_request_id})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'initiated')
        self.assertEqual(response.json()['checkout_request_id'], 'BOOTSTRAP_1')

    @patch('app.shop_launch_views.MpesaBootstrap.handle_callback')
    def test_mpesa_callback_activates_shop(self, mock_handle_callback):
        shop = Shop.objects.create(owner=self.user, name='Callback Shop', domain='callback-shop')
        Transaction.objects.create(
            user=self.user,
            shop=shop,
            action='shop_creation',
            amount=500,
            status='initiated',
            payment_method='mpesa',
            phone_number='254712345678',
            reference_id='SHOP-2-REF',
            mpesa_checkout_request_id='BOOTSTRAP_CALLBACK_1',
        )
        mock_handle_callback.return_value = {'success': True, 'receipt': 'ABC123'}

        payload = {
            'Body': {
                'stkCallback': {
                    'ResultCode': 0,
                    'CheckoutRequestID': 'BOOTSTRAP_CALLBACK_1',
                    'CallbackMetadata': {
                        'Item': [
                            {'Name': 'MpesaReceiptNumber', 'Value': 'ABC123'},
                        ]
                    },
                }
            }
        }

        response = self.client.post(
            reverse('shop_mpesa_callback'),
            data=json.dumps(payload),
            content_type='application/json',
        )

        shop.refresh_from_db()
        transaction = Transaction.objects.get(mpesa_checkout_request_id='BOOTSTRAP_CALLBACK_1')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['ResultCode'], 0)
        self.assertTrue(shop.is_active)
        self.assertEqual(transaction.status, 'success')
        self.assertEqual(transaction.mpesa_receipt, 'ABC123')
