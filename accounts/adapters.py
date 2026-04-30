"""Django-allauth adapter for custom account behavior."""

from allauth.account.adapter import DefaultAccountAdapter


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom adapter for django-allauth to customize behavior.
    """

    def save_user(self, request, sociallogin, form=None):
        """
        Custom user save - set email_verified for social logins.
        """
        user = super().save_user(request, sociallogin, form)
        
        # Auto-verify email for social logins
        if sociallogin:
            user.emailaddress_set.filter(primary=True).update(verified=True)
        
        return user

    def populate_user(self, request, sociallogin, data):
        """
        Populate user from social login data.
        """
        user = super().populate_user(request, sociallogin, data)
        # Set a default role for social logins
        if not hasattr(user, 'role') or not user.role:
            user.role = 'buyer'
        return user
