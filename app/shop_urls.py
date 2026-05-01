"""
Shop URL generation and management utilities.
Handles generating URLs for shops based on different routing strategies.
"""

from django.utils.text import slugify
from django.conf import settings


def generate_shop_slug(shop_name):
    """
    Generate a URL-safe slug from shop name.
    
    Args:
        shop_name: Shop name to slugify
    
    Returns:
        str: URL-safe slug
    """
    return slugify(shop_name)


def get_shop_url(shop):
    """
    Get the full URL for a shop storefront.
    
    Current strategy: https://shopname.smw.pgwiz.cloud/ or https://username.smw.pgwiz.cloud/shopname/
    
    Args:
        shop: Shop object
    
    Returns:
        dict: {
            'subdomain_url': 'https://shopname.smw.pgwiz.cloud/',
            'owner_url': 'https://username.smw.pgwiz.cloud/shopname/',
            'main_site_url': 'https://smw.pgwiz.cloud/shop/shopname/'
        }
    """
    shop_slug = generate_shop_slug(shop.name)
    owner_username = shop.owner.username
    
    # Get domain from settings or use default
    domain = getattr(settings, 'PRIMARY_DOMAIN', 'smw.pgwiz.cloud')
    protocol = 'https' if not settings.DEBUG else 'http'
    
    urls = {
        # Option 1: Shop subdomain
        'subdomain_url': f"{protocol}://{shop_slug}.{domain}/",
        
        # Option 2: Owner subdomain with shop path
        'owner_url': f"{protocol}://{owner_username}.{domain}/{shop_slug}/",
        
        # Option 3: Main site with shop path
        'main_site_url': f"{protocol}://{domain}/shop/{owner_username}/{shop_slug}/",
        
        # Preferred URL (subdomain - easiest for branding)
        'preferred': f"{protocol}://{shop_slug}.{domain}/"
    }
    
    return urls


def get_shop_from_request(request):
    """
    Extract shop from the request based on subdomain or URL path.
    
    Args:
        request: Django request object
    
    Returns:
        Shop object or None if not found
    """
    from mydak.models import Shop
    
    host = request.get_host().split(':')[0]  # Remove port
    parts = host.split('.')
    
    # Check if this is a shop subdomain (shopname.smw.pgwiz.cloud)
    if len(parts) > 3:
        shop_identifier = parts[0]
        
        try:
            # Try to find by shop name
            shop = Shop.objects.get(name__iexact=shop_identifier, is_active=True)
            return shop
        except Shop.DoesNotExist:
            # Try to find by owner username
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                owner = User.objects.get(username=shop_identifier)
                # Return first active shop for this owner
                return Shop.objects.filter(owner=owner, is_active=True).first()
            except User.DoesNotExist:
                return None
    
    return None


def validate_shop_slug(slug):
    """
    Validate if a shop slug is available/valid.
    
    Args:
        slug: URL slug to check
    
    Returns:
        dict: {
            'valid': bool,
            'error': str or None,
            'available': bool  # True if slug is available
        }
    """
    from mydak.models import Shop
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Check length
    if len(slug) < 3:
        return {
            'valid': False,
            'error': 'Slug must be at least 3 characters long',
            'available': False
        }
    
    if len(slug) > 50:
        return {
            'valid': False,
            'error': 'Slug must be 50 characters or less',
            'available': False
        }
    
    # Check if already used by shop
    if Shop.objects.filter(name__iexact=slug).exists():
        return {
            'valid': False,
            'error': 'This shop name is already taken',
            'available': False
        }
    
    # Check if already used as username
    if User.objects.filter(username=slug).exists():
        return {
            'valid': False,
            'error': 'This username is already taken',
            'available': False
        }
    
    # Check for reserved words
    reserved_words = ['admin', 'api', 'www', 'mail', 'ftp', 'shop', 'shops', 'dashboard', 'seller', 'account', 'accounts', 'login', 'register', 'auth', 'payment', 'cart', 'checkout']
    if slug.lower() in reserved_words:
        return {
            'valid': False,
            'error': f'"{slug}" is a reserved word and cannot be used',
            'available': False
        }
    
    return {
        'valid': True,
        'error': None,
        'available': True
    }
