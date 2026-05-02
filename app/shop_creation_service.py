"""Service helpers for the shop creation wizard launch flow."""

from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction

from mydak.models import Shop, Transaction
from mydak.mpesa import MpesaBootstrap, get_transaction_amount

from app.shop_urls import generate_shop_slug


class ShopCreationService:
    """Create and finalize draft shops through the payment flow."""

    @staticmethod
    def build_payload(data):
        """Normalize POST data into a payload dictionary."""
        return {
            'name': (data.get('shop_name') or '').strip(),
            'description': (data.get('description') or '').strip(),
            'category': (data.get('category') or '').strip(),
            'location': (data.get('location') or '').strip(),
            'theme_id': (data.get('theme_id') or 'campus_light').strip(),
            'accent_color': (data.get('accent_color') or '').strip(),
            'banner_preset': (data.get('banner_preset') or '').strip(),
            'tagline': (data.get('tagline') or '').strip(),
            'affiliation_mode': (data.get('affiliation_mode') or 'skip').strip(),
            'university_id': (data.get('university_id') or '').strip(),
            'location_id': (data.get('location_id') or '').strip(),
            'verification_email': (data.get('verification_email') or '').strip(),
            'email_verified': str(data.get('email_verified') or '').lower() in {'1', 'true', 'yes', 'on'},
            'whatsapp': (data.get('whatsapp') or '').strip(),
            'instagram': (data.get('instagram') or '').strip(),
            'tiktok': (data.get('tiktok') or '').strip(),
            'twitter': (data.get('twitter') or '').strip(),
            'payment_phone': (data.get('payment_phone') or '').strip(),
            'slug': generate_shop_slug(data.get('shop_name') or ''),
        }

    @staticmethod
    def _unique_domain(shop_name):
        base_slug = generate_shop_slug(shop_name)
        if not base_slug:
            raise ValidationError('Shop name is required.')

        candidate = base_slug
        suffix = 2
        while Shop.objects.filter(domain__iexact=candidate).exists():
            candidate = f'{base_slug}-{suffix}'
            suffix += 1
        return candidate

    @staticmethod
    def _normalize_phone(phone):
        phone = (phone or '').strip().replace(' ', '')
        if phone.startswith('+'):
            phone = phone[1:]
        if phone.startswith('0'):
            phone = f'254{phone[1:]}'
        return phone

    @classmethod
    def validate_payload(cls, payload):
        errors = {}
        if len(payload['name']) < 3:
            errors['shop_name'] = 'Shop name must be at least 3 characters.'
        if not payload['category']:
            errors['category'] = 'Please select a category.'
        if len(payload['description']) < 20:
            errors['description'] = 'Please add a description of at least 20 characters.'
        if len(payload['whatsapp']) < 8:
            errors['whatsapp'] = 'Please provide a WhatsApp number.'
        if len(payload['payment_phone']) < 8:
            errors['payment_phone'] = 'Please provide the M-Pesa phone number.'
        if payload['affiliation_mode'] not in {'skip', 'university', 'location'}:
            errors['affiliation_mode'] = 'Invalid affiliation mode.'
        if errors:
            raise ValidationError(errors)

    @classmethod
    def launch_shop(cls, user, payload, files):
        """Create a draft shop, create a payment transaction, and initiate STK."""
        cls.validate_payload(payload)

        phone_number = cls._normalize_phone(payload['payment_phone'])
        if len(phone_number) != 12 or not phone_number.startswith('254'):
            raise ValidationError({'payment_phone': 'Use a Kenyan number in 2547XXXXXXXX format.'})

        with db_transaction.atomic():
            domain = cls._unique_domain(payload['name'])
            shop = Shop.objects.create(
                owner=user,
                name=payload['name'],
                domain=domain,
                description=payload['description'],
                theme_id=payload['theme_id'] or 'campus_light',
                is_active=False,
            )

            if files and files.get('logo'):
                shop.logo = files['logo']
                shop.save(update_fields=['logo'])

            transaction = Transaction.objects.create(
                user=user,
                shop=shop,
                action='shop_creation',
                amount=get_transaction_amount('shop_creation'),
                status='pending',
                payment_method='mpesa',
                phone_number=phone_number,
                reference_id=f'SHOP-{shop.id}-{uuid4().hex[:12]}',
                metadata={
                    'shop_id': shop.id,
                    'payload': payload,
                },
            )

            mpesa = MpesaBootstrap()
            result = mpesa.initiate_stk_push(
                phone=phone_number,
                amount=int(transaction.amount),
                transaction_id=transaction.id,
                description=f'Shop creation - {shop.name}',
            )

            if 'error' in result:
                raise ValidationError({'payment_phone': result['error']})

            transaction.mpesa_checkout_request_id = result.get('checkout_request_id')
            transaction.metadata = {
                **transaction.metadata,
                'mpesa': result,
            }
            transaction.mark_as_initiated()
            transaction.save(update_fields=['mpesa_checkout_request_id', 'metadata', 'status', 'initiated_at', 'updated_at'])

            return shop, transaction, result

    @staticmethod
    def activate_shop_from_transaction(transaction):
        """Activate the shop linked to a successful transaction."""
        shop = transaction.shop
        if not shop:
            return None

        if not shop.is_active:
            shop.is_active = True
            shop.save(update_fields=['is_active', 'updated_at'])

        transaction.metadata = {
            **(transaction.metadata or {}),
            'activated_shop_id': shop.id,
        }
        transaction.save(update_fields=['metadata', 'updated_at'])
        return shop
