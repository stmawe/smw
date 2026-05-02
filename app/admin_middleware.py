"""
Middleware to route admin.smw.pgwiz.cloud to admin URL config
Bypasses django-tenants routing for the admin subdomain.
"""
from django.http import HttpResponseNotFound
from django.urls import resolve, Resolver404


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
            
            # Try to resolve the URL using admin patterns directly
            try:
                from django.urls import resolve as django_resolve
                match = django_resolve(request.path_info, urlconf='app.admin_urls')
                # URL is valid, proceed
            except Resolver404:
                # URL doesn't match any admin pattern, return 404
                return HttpResponseNotFound(f'Admin endpoint not found: {request.path_info}')
        else:
            request.is_admin_subdomain = False
        
        response = self.get_response(request)
        return response

