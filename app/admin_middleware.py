"""
Middleware to route admin.smw.pgwiz.cloud to admin URL config
Bypasses django-tenants routing for the admin subdomain.
"""
import logging
from django.http import HttpResponseNotFound
from django.urls import resolve, Resolver404

logger = logging.getLogger(__name__)


class AdminSubdomainMiddleware:
    """
    Routes admin.smw.pgwiz.cloud to the admin URL configuration.
    Handles routing directly without django-tenants involvement.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Load admin patterns once
        from app.admin_urls import admin_subdomain_patterns
        self.admin_patterns = admin_subdomain_patterns
    
    def __call__(self, request):
        # Check if this is the admin subdomain
        host = request.get_host().split(':')[0]  # Remove port if present
        
        if host == 'admin.smw.pgwiz.cloud':
            request.is_admin_subdomain = True
            # Override urlconf with admin patterns
            request.urlconf = 'app.admin_urls'
            logger.info(f"[ADMIN] Request to {host}{request.path_info} - urlconf set to app.admin_urls")
            
            # Try to resolve the URL using admin patterns directly
            try:
                from django.urls import resolve as django_resolve
                match = django_resolve(request.path_info, urlconf='app.admin_urls')
                logger.info(f"[ADMIN] URL resolved to {match.func.__name__}")
            except Resolver404:
                logger.warning(f"[ADMIN] URL {request.path_info} not found in admin patterns")
                # URL doesn't match any admin pattern, proceed anyway and let Django handle 404
        else:
            request.is_admin_subdomain = False
        
        response = self.get_response(request)
        return response

