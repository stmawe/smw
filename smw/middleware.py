"""
Subdomain middleware for multi-tenant routing.
Detects subdomain and adds it to request for views to use.
"""

from django.http import HttpResponseNotFound


class SubdomainMiddleware:
    """
    Middleware to detect subdomain and add to request.
    Allows views to act based on which subdomain was accessed.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Extract subdomain from host
        host = request.get_host().split(':')[0]  # Remove port if present
        
        # Parse subdomain
        subdomain_info = self._parse_subdomain(host)
        request.subdomain = subdomain_info['subdomain']
        request.subdomain_type = subdomain_info['type']
        request.subdomain_identifier = subdomain_info['identifier']
        
        # Add boolean flags for convenience
        request.is_admin_subdomain = subdomain_info['type'] == 'admin'
        request.is_shop_subdomain = subdomain_info['type'] in ('shop', 'user')
        
        response = self.get_response(request)
        return response
    
    def _parse_subdomain(self, host):
        """
        Parse hostname and determine subdomain type.
        
        Returns:
            dict with keys:
            - subdomain: The subdomain part (e.g., 'admin', 'shop-name')
            - type: One of 'admin', 'shop', 'user', 'main'
            - identifier: The identifier if applicable
        """
        # Remove port
        host = host.split(':')[0]
        
        # Check if localhost
        if host in ('localhost', '127.0.0.1', '[::1]'):
            return {'subdomain': 'localhost', 'type': 'main', 'identifier': None}
        
        parts = host.split('.')
        
        # Domains without subdomains
        if len(parts) <= 2:
            return {'subdomain': None, 'type': 'main', 'identifier': None}
        
        # Check for .pgwiz.cloud or .smw.pgwiz.cloud
        if parts[-2:] == ['pgwiz', 'cloud']:
            subdomain = parts[0]
            
            # Admin subdomain
            if subdomain.lower() == 'admin':
                return {'subdomain': 'admin', 'type': 'admin', 'identifier': None}
            
            # Any other subdomain is treated as shop/user
            return {'subdomain': subdomain, 'type': 'shop', 'identifier': subdomain}
        
        # Default to main
        return {'subdomain': None, 'type': 'main', 'identifier': None}

