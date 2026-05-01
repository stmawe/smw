"""
Middleware to route admin.smw.pgwiz.cloud to admin URL config
"""
from types import ModuleType


class AdminSubdomainMiddleware:
    """
    Routes admin.smw.pgwiz.cloud to the admin URL configuration.
    This solves django-tenants not recognizing the admin subdomain.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Load admin patterns once
        from app.admin_urls import admin_subdomain_patterns
        
        # Create a module-like object with urlpatterns
        self.admin_urlconf = ModuleType('admin_urlconf')
        self.admin_urlconf.urlpatterns = admin_subdomain_patterns
    
    def __call__(self, request):
        # Check if this is the admin subdomain
        host = request.get_host().split(':')[0]  # Remove port if present
        
        if host == 'admin.smw.pgwiz.cloud':
            request.is_admin_subdomain = True
            # Replace the urlconf for this request
            request.urlconf = self.admin_urlconf
        else:
            request.is_admin_subdomain = False
        
        response = self.get_response(request)
        return response

