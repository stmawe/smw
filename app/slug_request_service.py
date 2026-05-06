"""
SlugRequestService — handles Tier 1 (root promotion) and Tier 2 (custom slug) requests.

Tier 1 — root_promotion:
    User requests their shop serve at {username}.smw.pgwiz.cloud/ (the root).
    Only one shop per user can hold root at a time.

Tier 2 — custom_slug:
    User requests a cleaner/custom path segment for their shop.
    e.g. change 'juju-electronics' → 'electronics'

Both require admin approval. Payment reference is stored if payment was collected
before submission, but STK push logic is NOT touched here.
"""

import logging

from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction

logger = logging.getLogger(__name__)


class SlugRequestService:
    """Service for creating and reviewing ShopSlugRequests."""

    # ------------------------------------------------------------------ #
    # Submission                                                           #
    # ------------------------------------------------------------------ #

    @staticmethod
    def submit_root_promotion(shop, payment_reference=None):
        """
        Submit a Tier 1 root-promotion request for a shop.

        Args:
            shop: mydak.Shop instance
            payment_reference: Optional M-Pesa payment reference string

        Returns:
            ShopSlugRequest instance (status=pending)

        Raises:
            ValidationError if a pending root-promotion request already exists
            for any shop owned by the same user.
        """
        from mydak.models import ShopSlugRequest

        # Block if user already has a pending root-promotion request on any shop
        owner_shop_ids = shop.owner.shops.values_list('id', flat=True)
        if ShopSlugRequest.objects.filter(
            shop_id__in=owner_shop_ids,
            request_type='root_promotion',
            status='pending',
        ).exists():
            raise ValidationError(
                'You already have a pending root-promotion request. '
                'Wait for it to be reviewed before submitting another.'
            )

        req = ShopSlugRequest(
            shop=shop,
            request_type='root_promotion',
            status='pending',
            payment_reference=payment_reference or '',
        )
        req.full_clean()
        req.save()
        logger.info('Root-promotion request submitted for shop %s (id=%s)', shop.name, shop.id)
        return req

    @staticmethod
    def submit_custom_slug(shop, requested_slug, payment_reference=None):
        """
        Submit a Tier 2 custom-slug request for a shop.

        Args:
            shop: mydak.Shop instance
            requested_slug: The desired new slug string
            payment_reference: Optional M-Pesa payment reference string

        Returns:
            ShopSlugRequest instance (status=pending)

        Raises:
            ValidationError if requested_slug is invalid or a pending custom-slug
            request already exists for this shop.
        """
        from mydak.models import ShopSlugRequest
        from app.shop_urls import validate_shop_slug

        # Validate the requested slug (per-user scope)
        result = validate_shop_slug(requested_slug, user=shop.owner)
        if not result['valid']:
            raise ValidationError({'requested_slug': result['error']})

        req = ShopSlugRequest(
            shop=shop,
            request_type='custom_slug',
            requested_slug=result['slug'],
            status='pending',
            payment_reference=payment_reference or '',
        )
        req.full_clean()
        req.save()
        logger.info(
            'Custom-slug request submitted for shop %s (id=%s): "%s"',
            shop.name, shop.id, result['slug'],
        )
        return req

    # ------------------------------------------------------------------ #
    # Admin review                                                         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def approve_request(request_obj, reviewer):
        """
        Approve a pending ShopSlugRequest.

        Dispatches to the appropriate approval handler based on request_type.
        Uses db_transaction.atomic() to ensure consistency.

        Args:
            request_obj: ShopSlugRequest instance with status='pending'
            reviewer: User instance (admin who is approving)

        Raises:
            ValidationError if request is not in pending status.
        """
        if request_obj.status != 'pending':
            raise ValidationError(f'Cannot approve a request with status "{request_obj.status}".')

        if request_obj.request_type == 'root_promotion':
            SlugRequestService._approve_root_promotion(request_obj, reviewer)
        elif request_obj.request_type == 'custom_slug':
            SlugRequestService._approve_custom_slug(request_obj, reviewer)
        else:
            raise ValidationError(f'Unknown request_type: {request_obj.request_type}')

    @staticmethod
    def reject_request(request_obj, reviewer, reason):
        """
        Reject a pending ShopSlugRequest.

        Args:
            request_obj: ShopSlugRequest instance with status='pending'
            reviewer: User instance (admin who is rejecting)
            reason: Non-empty string explaining the rejection

        Raises:
            ValidationError if reason is empty or request is not pending.
        """
        if request_obj.status != 'pending':
            raise ValidationError(f'Cannot reject a request with status "{request_obj.status}".')

        if not (reason or '').strip():
            raise ValidationError({'reviewer_notes': 'A rejection reason is required.'})

        request_obj.status = 'rejected'
        request_obj.admin_reviewer = reviewer
        request_obj.reviewer_notes = reason.strip()
        request_obj.save(update_fields=['status', 'admin_reviewer', 'reviewer_notes', 'updated_at'])
        logger.info(
            'Slug request %s rejected by %s: %s',
            request_obj.id, reviewer.username, reason[:80],
        )

    # ------------------------------------------------------------------ #
    # Internal approval handlers                                           #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _approve_root_promotion(request_obj, reviewer):
        """
        Atomically promote a shop to root and clear all sibling root flags.
        """
        from mydak.models import Shop

        with db_transaction.atomic():
            shop = Shop.objects.select_for_update().get(pk=request_obj.shop_id)

            # Clear is_root_shop on all other shops owned by this user
            Shop.objects.filter(
                owner=shop.owner,
                is_root_shop=True,
            ).exclude(pk=shop.pk).update(is_root_shop=False)

            shop.is_root_shop = True
            shop.save(update_fields=['is_root_shop', 'updated_at'])

            request_obj.status = 'approved'
            request_obj.admin_reviewer = reviewer
            request_obj.save(update_fields=['status', 'admin_reviewer', 'updated_at'])

        logger.info(
            'Root-promotion approved for shop %s (id=%s) by %s',
            shop.name, shop.id, reviewer.username,
        )

    @staticmethod
    def _approve_custom_slug(request_obj, reviewer):
        """
        Approve a custom-slug request.

        Re-validates uniqueness at approval time — if a conflict has arisen since
        submission, auto-rejects with a descriptive note instead of raising.
        """
        from mydak.models import Shop
        from app.shop_urls import validate_shop_slug

        with db_transaction.atomic():
            shop = Shop.objects.select_for_update().get(pk=request_obj.shop_id)
            requested = request_obj.requested_slug

            # Re-check uniqueness at approval time (Req 8.5)
            result = validate_shop_slug(requested, user=shop.owner)
            if not result['valid']:
                # Conflict arose since submission — auto-reject
                request_obj.status = 'rejected'
                request_obj.admin_reviewer = reviewer
                request_obj.reviewer_notes = (
                    f'Auto-rejected at approval time: slug "{requested}" is no longer available. '
                    f'{result["error"] or ""}'
                ).strip()
                request_obj.save(update_fields=['status', 'admin_reviewer', 'reviewer_notes', 'updated_at'])
                logger.warning(
                    'Custom-slug request %s auto-rejected at approval: slug "%s" conflict',
                    request_obj.id, requested,
                )
                return

            shop.domain = requested
            shop.slug_approved = True
            shop.save(update_fields=['domain', 'slug_approved', 'updated_at'])

            request_obj.status = 'approved'
            request_obj.admin_reviewer = reviewer
            request_obj.save(update_fields=['status', 'admin_reviewer', 'updated_at'])

        logger.info(
            'Custom-slug approved for shop %s (id=%s): "%s" by %s',
            shop.name, shop.id, requested, reviewer.username,
        )
