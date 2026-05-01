"""
Admin Audit Logging via Django Signals
Automatically log all model changes without explicit calls.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
import json

from .models import AdminAuditLog, AdminActivityFeed
from mydak.models import Shop, Listing, Transaction, Category

User = get_user_model()


# Track original values before change
_original_values = {}


def track_original_values(sender, instance, **kwargs):
    """
    Pre-save signal to capture original values.
    Called before save to compare with new values.
    """
    if kwargs.get('created'):
        # New instance, no original values
        _original_values[id(instance)] = {}
    else:
        # Existing instance, capture current values
        try:
            original = sender.objects.get(pk=instance.pk)
            _original_values[id(instance)] = {
                f.name: getattr(original, f.name)
                for f in sender._meta.get_fields()
                if hasattr(f, 'attname') and not f.many_to_one and not f.one_to_many
            }
        except sender.DoesNotExist:
            _original_values[id(instance)] = {}


def get_original_values(instance):
    """Retrieve and clean up original values."""
    instance_id = id(instance)
    original = _original_values.pop(instance_id, {})
    return original


# ============================================================
# USER MODEL SIGNALS
# ============================================================

@receiver(post_save, sender=User)
def log_user_change(sender, instance, created, **kwargs):
    """Log user create/update actions."""
    # Skip superuser and staff changes during initial setup
    if not hasattr(instance, '_audit_skip'):
        action = 'create' if created else 'update'
        
        AdminActivityFeed.objects.create(
            admin_user=None,  # System-generated
            activity_type='created' if created else 'updated',
            content_type='User',
            object_id=str(instance.id),
            object_title=instance.email,
            description=f"User {action}: {instance.email}",
            severity='info',
        )


@receiver(post_delete, sender=User)
def log_user_delete(sender, instance, **kwargs):
    """Log user deletion."""
    AdminActivityFeed.objects.create(
        admin_user=None,
        activity_type='deleted',
        content_type='User',
        object_id=str(instance.id),
        object_title=instance.email,
        description=f"User deleted: {instance.email}",
        severity='warning',
    )


# ============================================================
# SHOP MODEL SIGNALS
# ============================================================

@receiver(post_save, sender=Shop)
def log_shop_change(sender, instance, created, **kwargs):
    """Log shop create/update actions."""
    action = 'created' if created else 'updated'
    
    AdminActivityFeed.objects.create(
        admin_user=None,
        activity_type='created' if created else 'updated',
        content_type='Shop',
        object_id=str(instance.id),
        object_title=instance.name,
        description=f"Shop {action}: {instance.name}",
        severity='info',
    )


@receiver(post_delete, sender=Shop)
def log_shop_delete(sender, instance, **kwargs):
    """Log shop deletion."""
    AdminActivityFeed.objects.create(
        admin_user=None,
        activity_type='deleted',
        content_type='Shop',
        object_id=str(instance.id),
        object_title=instance.name,
        description=f"Shop deleted: {instance.name}",
        severity='warning',
    )


# ============================================================
# LISTING MODEL SIGNALS
# ============================================================

@receiver(post_save, sender=Listing)
def log_listing_change(sender, instance, created, **kwargs):
    """Log listing create/update actions."""
    action = 'created' if created else 'updated'
    title = instance.title if hasattr(instance, 'title') else f'Listing #{instance.id}'
    
    AdminActivityFeed.objects.create(
        admin_user=None,
        activity_type='created' if created else 'updated',
        content_type='Listing',
        object_id=str(instance.id),
        object_title=title,
        description=f"Listing {action}: {title}",
        severity='info',
    )


@receiver(post_delete, sender=Listing)
def log_listing_delete(sender, instance, **kwargs):
    """Log listing deletion."""
    title = instance.title if hasattr(instance, 'title') else f'Listing #{instance.id}'
    
    AdminActivityFeed.objects.create(
        admin_user=None,
        activity_type='deleted',
        content_type='Listing',
        object_id=str(instance.id),
        object_title=title,
        description=f"Listing deleted: {title}",
        severity='warning',
    )


# ============================================================
# TRANSACTION MODEL SIGNALS
# ============================================================

@receiver(post_save, sender=Transaction)
def log_transaction_change(sender, instance, created, **kwargs):
    """Log transaction create/update actions."""
    action = 'created' if created else 'updated'
    trans_id = instance.transaction_id if hasattr(instance, 'transaction_id') else str(instance.id)
    
    AdminActivityFeed.objects.create(
        admin_user=None,
        activity_type='created' if created else 'updated',
        content_type='Transaction',
        object_id=str(instance.id),
        object_title=f"Transaction {trans_id}",
        description=f"Transaction {action}: {trans_id}",
        severity='info',
    )


# ============================================================
# CATEGORY MODEL SIGNALS
# ============================================================

@receiver(post_save, sender=Category)
def log_category_change(sender, instance, created, **kwargs):
    """Log category create/update actions."""
    action = 'created' if created else 'updated'
    
    AdminActivityFeed.objects.create(
        admin_user=None,
        activity_type='created' if created else 'updated',
        content_type='Category',
        object_id=str(instance.id),
        object_title=instance.name,
        description=f"Category {action}: {instance.name}",
        severity='info',
    )


@receiver(post_delete, sender=Category)
def log_category_delete(sender, instance, **kwargs):
    """Log category deletion."""
    AdminActivityFeed.objects.create(
        admin_user=None,
        activity_type='deleted',
        content_type='Category',
        object_id=str(instance.id),
        object_title=instance.name,
        description=f"Category deleted: {instance.name}",
        severity='warning',
    )
