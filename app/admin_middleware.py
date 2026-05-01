"""
Middleware to detect admin subdomain and route accordingly
"""

class AdminSubdomainMiddleware:
    """
    Detects admin.smw.pgwiz.cloud and sets a flag for admin context
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if this is the admin subdomain
        host = request.get_host().split(':')[0]  # Remove port if present
        
        if host in ['admin.smw.pgwiz.cloud', 'admin.smw.pgwiz.cloud:443']:
            request.is_admin_subdomain = True
        else:
            request.is_admin_subdomain = False
        
        response = self.get_response(request)
        return response
