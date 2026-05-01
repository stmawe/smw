"""
Shop URL endpoints and utilities.
Provides API and views for managing shop URLs and sharing.
"""

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from mydak.models import Shop
from app.shop_urls import get_shop_url, validate_shop_slug


@login_required
def shop_url_api(request, shop_id):
    """
    API endpoint to get shop URL information.
    Returns the full shop URLs in JSON format.
    
    Example: GET /api/shop/1/url/
    Returns:
    {
        "shop_id": 1,
        "shop_name": "Fashion Hub",
        "urls": {
            "subdomain": "https://fashion-hub.smw.pgwiz.cloud/",
            "owner": "https://johndoe.smw.pgwiz.cloud/fashion-hub/",
            "main_site": "https://smw.pgwiz.cloud/shop/johndoe/fashion-hub/"
        },
        "preferred": "https://fashion-hub.smw.pgwiz.cloud/",
        "social_share": {
            "twitter": "https://twitter.com/intent/tweet?url=...",
            "facebook": "https://facebook.com/sharer.php?u=..."
        }
    }
    """
    shop = get_object_or_404(Shop, id=shop_id)
    
    # Check permissions
    if shop.owner != request.user and not request.user.is_superuser:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    urls = get_shop_url(shop)
    preferred_url = urls['preferred']
    
    response_data = {
        'shop_id': shop.id,
        'shop_name': shop.name,
        'urls': {
            'subdomain': urls['subdomain_url'],
            'owner': urls['owner_url'],
            'main_site': urls['main_site_url']
        },
        'preferred': preferred_url,
        'social_share': {
            'twitter': f"https://twitter.com/intent/tweet?url={preferred_url}&text=Check%20out%20{shop.name}%20on%20SMW",
            'facebook': f"https://facebook.com/sharer.php?u={preferred_url}",
            'whatsapp': f"https://wa.me/?text={shop.name}%20{preferred_url}"
        },
        'is_active': shop.is_active,
        'created': shop.created_at.isoformat() if shop.created_at else None
    }
    
    return JsonResponse(response_data)


@login_required
def shop_sharing_page(request, shop_id):
    """
    Display shop sharing page with copyable URLs and social share buttons.
    """
    shop = get_object_or_404(Shop, id=shop_id)
    
    # Check permissions
    if shop.owner != request.user and not request.user.is_superuser:
        return render(request, '403.html', status=403)
    
    urls = get_shop_url(shop)
    
    context = {
        'shop': shop,
        'urls': urls,
        'preferred_url': urls['preferred'],
        'social_urls': {
            'twitter': f"https://twitter.com/intent/tweet?url={urls['preferred']}&text=Check%20out%20{shop.name}",
            'facebook': f"https://facebook.com/sharer.php?u={urls['preferred']}",
            'whatsapp': f"https://wa.me/?text={shop.name}%20{urls['preferred']}"
        }
    }
    
    return render(request, 'shop_sharing.html', context)


def validate_shop_slug_api(request):
    """
    API endpoint to validate shop slug availability.
    GET /api/validate-slug/?slug=fashion-hub
    
    Returns:
    {
        "valid": true/false,
        "available": true/false,
        "error": "error message or null"
    }
    """
    slug = request.GET.get('slug', '').strip()
    
    if not slug:
        return JsonResponse({
            'valid': False,
            'available': False,
            'error': 'Slug is required'
        })
    
    result = validate_shop_slug(slug)
    return JsonResponse(result)
