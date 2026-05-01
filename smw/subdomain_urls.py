"""
Subdomain-based URL routing for multi-tenant setup.
Routes requests to different URL patterns based on subdomain.
"""

from django.urls import path, include
from app.admin_urls import admin_subdomain_patterns

def get_urlpatterns(request):
    """
    Determine URL patterns based on subdomain.
    This is called for each request to dynamically route based on host.
    """
    host = request.get_host().split(':')[0]  # Remove port
    
    # Check if this is the admin subdomain (admin.smw.pgwiz.cloud)
    if host.startswith('admin.'):
        return admin_subdomain_patterns
    
    # Check if this is a shop subdomain or owner subdomain
    # Format: shopname.smw.pgwiz.cloud or username.smw.pgwiz.cloud
    parts = host.split('.')
    if len(parts) > 2 and parts[-2:] == ['pgwiz', 'cloud']:
        # This is a subdomain request, route to shop views
        from mydak.urls import shop_subdomain_patterns
        return shop_subdomain_patterns
    
    # Default to main app URLs
    from app.urls import urlpatterns
    return urlpatterns
