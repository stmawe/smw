"""Signals for accounts app."""

from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.account.signals import email_confirmed
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(email_confirmed)
def email_confirmed_handler(sender, request, email_address, **kwargs):
    """
    Handler for email confirmation.
    """
    # Email is now verified, could send welcome email or update user
    user = email_address.user
    user.is_active = True
    user.save()
