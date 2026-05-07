"""
Tenant URL routing views for shop storefront dispatch.

These views handle requests that arrive at a user's personal subdomain:
    {username}.smw.pgwiz.cloud/              → tenant_root_view
    {username}.smw.pgwiz.cloud/{shop_slug}/  → shop_storefront_view

django-tenants middleware has already resolved the tenant schema from the
hostname before these views are called.
"""

import logging

from django.http import Http404
from django.shortcuts import get_object_or_404, render

from .models import Shop

logger = logging.getLogger(__name__)


def _resolve_owner_from_request(request):
    """
    Derive the owner User from the current request hostname.

    The hostname is {username}.{base_domain}. We extract the username
    (first subdomain segment) and look up the User.

    Returns User or None.
    """
    from django.conf import settings
    from django.contrib.auth import get_user_model

    User = get_user_model()
    host = request.get_host().split(':')[0]  # strip port
    base_domain = getattr(settings, 'BASE_DOMAIN', 'smw.pgwiz.cloud')

    # Strip the base domain to get the subdomain portion
    if host.endswith(f'.{base_domain}'):
        subdomain = host[: -(len(base_domain) + 1)]  # e.g. "juju254"
        username = subdomain.split('.')[0]            # first segment only
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            logger.warning('tenant_root_view: no user found for subdomain "%s"', subdomain)
            return None

    return None


def tenant_root_view(request):
    """
    Serve the root path of a user's subdomain.

    Logic:
      1. Resolve the owner from the hostname.
      2. If the owner has a shop with is_root_shop=True and is_active=True,
         serve that shop's storefront.
      3. Otherwise, serve the user's profile page listing all active shops.
    """
    owner = _resolve_owner_from_request(request)

    if owner is None:
        # Hostname doesn't match a known user — fall through to 404
        raise Http404('No user found for this subdomain.')

    # Check for a root-promoted shop
    root_shop = Shop.objects.filter(
        owner=owner,
        is_root_shop=True,
        is_active=True,
    ).first()

    if root_shop:
        return _render_shop_storefront(request, root_shop)

    # No root shop — render the user's profile/shop-list page
    active_shops = Shop.objects.filter(owner=owner, is_active=True).order_by('name')
    return render(request, 'shops/user_profile.html', {
        'profile_owner': owner,
        'shops': active_shops,
    })


def seller_dashboard_view(request):
    """
    Private seller dashboard at {username}.smw.pgwiz.cloud/dashboard/

    Requires login. Shows the owner's shops, listings summary, and quick actions.
    If not logged in, redirects to the main site login.
    """
    from django.conf import settings as _s

    if not request.user.is_authenticated:
        protocol = 'http' if _s.DEBUG else 'https'
        login_url = f'{protocol}://smw.pgwiz.cloud/accounts/login/?next={request.build_absolute_uri()}'
        from django.shortcuts import redirect as _redirect
        return _redirect(login_url)

    owner = _resolve_owner_from_request(request)

    # Ensure the logged-in user owns this subdomain
    if owner is None or request.user.pk != owner.pk:
        raise Http404('Dashboard not found.')

    active_shops = Shop.objects.filter(owner=owner, is_active=True).order_by('name')
    inactive_shops = Shop.objects.filter(owner=owner, is_active=False).order_by('name')
    has_root_shop = active_shops.filter(is_root_shop=True).exists()
    total_shops = active_shops.count() + inactive_shops.count()

    from app.shop_urls import get_user_tier, get_user_shop_limit
    user_tier = get_user_tier(owner)
    shop_limit = get_user_shop_limit(owner)

    return render(request, 'shops/dashboard.html', {
        'owner': owner,
        'active_shops': active_shops,
        'inactive_shops': inactive_shops,
        'total_shops': total_shops,
        'has_root_shop': has_root_shop,
        'can_create_shop': total_shops < shop_limit and not has_root_shop,
        'user_tier': user_tier,
        'shop_limit': shop_limit,
        'remaining_shops': shop_limit - total_shops,
    })


def shop_storefront_view(request, shop_slug):
    """
    Serve a specific shop storefront at /{shop_slug}/.

    Looks up the shop by domain=shop_slug within the resolved tenant's owner.
    Returns HTTP 404 for unknown or inactive slugs.
    """
    owner = _resolve_owner_from_request(request)

    if owner is None:
        raise Http404('No user found for this subdomain.')

    shop = get_object_or_404(Shop, owner=owner, domain=shop_slug, is_active=True)
    return _render_shop_storefront(request, shop)


def _render_shop_storefront(request, shop):
    """
    Render the shop storefront template with standard context.
    """
    from app.shop_urls import get_shop_url

    listings = shop.listings.filter(status='active').order_by('-created_at')[:20]
    shop_urls = get_shop_url(shop)

    context = {
        'shop': shop,
        'listings': listings,
        'canonical_url': shop_urls['canonical'],
        'owner': shop.owner,
    }
    return render(request, 'shops/storefront.html', context)
