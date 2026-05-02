"""
Development-only middleware to emulate admin login for testing locally.
This is ONLY for local development and is disabled in production.
"""
import logging

logger = logging.getLogger(__name__)


class DevAuthBypassMiddleware:
    """
    Emulates an authenticated admin user for local development testing.
    Only active when DEBUG=True and ALLOWED_HOSTS includes localhost.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Only active in DEBUG mode on localhost
        from django.conf import settings
        if settings.DEBUG and request.get_host().startswith('127.0.0.1') or request.get_host().startswith('localhost'):
            # Emulate authenticated admin user
            from django.contrib.auth.models import User, Permission
            from django.contrib.contenttypes.models import ContentType
            from app.models import AdminRole
            
            try:
                # Create or get admin user
                admin_user, created = User.objects.get_or_create(
                    username='dev_admin',
                    defaults={
                        'email': 'dev@local.test',
                        'is_staff': True,
                        'is_superuser': True,
                        'is_active': True,
                    }
                )
                
                if created:
                    logger.info("[DEV-AUTH] Created test admin user: dev_admin")
                
                # Ensure user is staff and superuser
                if not admin_user.is_staff or not admin_user.is_superuser:
                    admin_user.is_staff = True
                    admin_user.is_superuser = True
                    admin_user.save()
                
                # Attach user to request
                request.user = admin_user
                
                # Create dummy session
                from django.contrib.sessions.models import Session
                request.session = request.session or {}
                request.session['_auth_user_id'] = admin_user.id
                
                logger.debug(f"[DEV-AUTH] Emulated login for: {admin_user.username}")
                
            except Exception as e:
                logger.warning(f"[DEV-AUTH] Failed to emulate login: {e}")
        
        response = self.get_response(request)
        return response
