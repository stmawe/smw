"""
Middleware to route admin.smw.pgwiz.cloud to admin URL config
"""

class AdminSubdomainMiddleware:
    """
    Routes admin.smw.pgwiz.cloud to the admin URL configuration.
    This solves django-tenants not recognizing the admin subdomain.
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if this is the admin subdomain
        host = request.get_host().split(':')[0]  # Remove port if present
        
        if host == 'admin.smw.pgwiz.cloud':
            request.is_admin_subdomain = True
            # Use string path to admin URLs
            request.urlconf = 'app.admin_urls'
        else:
            request.is_admin_subdomain = False
        
        response = self.get_response(request)
        return response

