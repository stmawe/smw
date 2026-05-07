"""Shop URL generation and management utilities."""

import re

from django.conf import settings


def generate_shop_slug(shop_name):
    """
    Generate a URL-safe slug from shop name.
    
    Args:
        shop_name: Shop name to slugify
    
    Returns:
        str: URL-safe slug
    """
    if not shop_name:
        return ""

    slug = str(shop_name).lower().strip()
    slug = slug.replace("'", "").replace("`", "")
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug[:48].strip("-")


def get_shop_url(shop):
    """
    Get the canonical URL for a shop storefront.

    Tier-aware:
      - is_root_shop=True  → {protocol}://{owner_username}.{domain}/
      - is_root_shop=False → {protocol}://{owner_username}.{domain}/{shop_slug}/

    Args:
        shop: Shop instance

    Returns:
        dict: {
            'canonical': str,   ← preferred URL (always present)
            'owner_url': str,   ← path-based URL regardless of tier (for reference)
            'main_site_url': str,
        }
    """
    shop_slug = shop.domain or generate_shop_slug(shop.name)
    owner_username = shop.owner.username

    domain = getattr(settings, 'PRIMARY_DOMAIN', None) or getattr(settings, 'BASE_DOMAIN', 'smw.pgwiz.cloud')
    protocol = 'http' if settings.DEBUG else 'https'

    owner_base = f"{protocol}://{owner_username}.{domain}"
    path_url = f"{owner_base}/{shop_slug}/"
    root_url = f"{owner_base}/"
    main_site_url = f"{protocol}://{domain}/shop/{owner_username}/{shop_slug}/"

    canonical = root_url if getattr(shop, 'is_root_shop', False) else path_url

    return {
        'canonical': canonical,
        'owner_url': path_url,       # always the path-based URL
        'main_site_url': main_site_url,
        # Legacy keys kept for backward compatibility with existing templates
        'preferred': canonical,
        'subdomain_url': path_url,   # deprecated — owner subdomain, not shop subdomain
    }


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
            # Try to find by shop slug/domain first
            shop = Shop.objects.get(domain__iexact=shop_identifier, is_active=True)
            return shop
        except Shop.DoesNotExist:
            try:
                # Fallback to shop name for legacy records
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


def validate_shop_slug(slug, user=None):
    """
    Validate if a shop slug is available and valid.

    Args:
        slug: URL slug to check
        user: Optional User instance. When provided, uniqueness is scoped to
              that user's shops only (two different users may share the same slug).
              When None, global uniqueness is checked (backward-compatible).

    Returns:
        dict: {
            'valid': bool,
            'error': str or None,
            'available': bool,
            'slug': str,
            'suggestion': str or None,
        }
    """
    from mydak.models import Shop
    from django.contrib.auth import get_user_model
    User = get_user_model()
    normalized = generate_shop_slug(slug)
    reserved_words = [
        'admin', 'api', 'www', 'mail', 'ftp', 'shop', 'shops', 'dashboard',
        'seller', 'account', 'accounts', 'login', 'register', 'auth', 'payment',
        'cart', 'checkout'
    ]

    # Check length
    if len(normalized) < 3:
        return {
            'valid': False,
            'error': 'Slug must be at least 3 characters long',
            'available': False,
            'slug': normalized,
            'suggestion': None,
        }

    if len(normalized) > 48:
        return {
            'valid': False,
            'error': 'Slug must be 48 characters or less',
            'available': False,
            'slug': normalized,
            'suggestion': None,
        }

    def _is_slug_taken(candidate):
        """Check uniqueness — scoped to user when provided, global otherwise."""
        if user is not None:
            # Per-user scope: only conflict if same owner has this slug
            return Shop.objects.filter(owner=user, domain__iexact=candidate).exists()
        else:
            # Global scope (backward-compatible)
            if Shop.objects.filter(domain__iexact=candidate).exists():
                return True
            return any(
                generate_shop_slug(shop_name) == candidate
                for shop_name in Shop.objects.values_list('name', flat=True)
            )

    # Check if already used
    if _is_slug_taken(normalized):
        suggestion = f"{normalized}-2"
        while _is_slug_taken(suggestion) or (
            user is None and User.objects.filter(username__iexact=suggestion).exists()
        ) or suggestion in reserved_words:
            suffix = int(suggestion.rsplit('-', 1)[-1]) + 1 if '-' in suggestion and suggestion.rsplit('-', 1)[-1].isdigit() else 3
            suggestion = f"{normalized}-{suffix}"
        return {
            'valid': False,
            'error': 'This shop slug is already taken',
            'available': False,
            'slug': normalized,
            'suggestion': suggestion,
        }

    # When doing global check, also block slugs that match existing usernames
    if user is None and User.objects.filter(username__iexact=normalized).exists():
        return {
            'valid': False,
            'error': 'This username is already taken',
            'available': False,
            'slug': normalized,
            'suggestion': f"{normalized}-2",
        }

    # Check for reserved words
    if normalized in reserved_words:
        return {
            'valid': False,
            'error': f'"{normalized}" is a reserved word and cannot be used',
            'available': False,
            'slug': normalized,
            'suggestion': f"{normalized}-shop",
        }

    return {
        'valid': True,
        'error': None,
        'available': True,
        'slug': normalized,
        'suggestion': None,
    }


def get_user_tier(user):
    """
    Derive the user's current URL tier from their shop state.

    Tier 0 (default): no root shop, no custom slug — up to 2 shops
    Tier 1 (root):    has a shop with is_root_shop=True — max 1 shop
    Tier 2 (custom):  has a shop with slug_approved=True — up to 2 shops

    Returns: int (0, 1, or 2)
    """
    from mydak.models import Shop

    if Shop.objects.filter(owner=user, is_root_shop=True).exists():
        return 1
    if Shop.objects.filter(owner=user, slug_approved=True).exists():
        return 2
    return 0


def get_user_shop_limit(user):
    """
    Return the maximum number of shops allowed for this user based on their tier.

    Tier 0: 2 shops
    Tier 1: 1 shop (root-promoted — one shop serves at /)
    Tier 2: 2 shops (custom slug approved)
    """
    tier = get_user_tier(user)
    return 1 if tier == 1 else 2
