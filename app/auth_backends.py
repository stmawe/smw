"""
Custom authentication backends for SMW marketplace
Allows login with username or email
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class UsernameOrEmailBackend(ModelBackend):
    """
    Custom backend that allows authentication with either username or email.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate using username or email + password
        """
        try:
            # Try to find user by username first
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            try:
                # Try to find user by email
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                # Run the default password hasher to prevent timing attacks
                User().set_password(password)
                return None

        # Check if the password is correct
        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

    def get_user(self, user_id):
        """
        Get user by ID
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
