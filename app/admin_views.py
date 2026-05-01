"""
Admin subdomain views for https://admin.smw.pgwiz.cloud/
Provides admin dashboard and shop management for sellers.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from .models import User
from mydak.models import Shop


@login_required(login_url='login')
def admin_dashboard_view(request, username=None):
    """
    Admin dashboard main page.
    Shows overview of shops, sales, analytics.
    """
    # If username is specified, check if user has permission to view it
    if username:
        target_user = get_object_or_404(User, username=username)
        # Only allow viewing own dashboard unless superuser
        if request.user != target_user and not request.user.is_superuser:
            messages.error(request, 'You do not have permission to view this dashboard.')
            return redirect('admin_dashboard')
        user = target_user
    else:
        user = request.user
    
    # Get user's shops
    shops = Shop.objects.filter(owner=user)
    
    # Get basic stats
    context = {
        'target_user': user,
        'shops': shops,
        'shop_count': shops.count(),
        'total_listings': sum(shop.listing_set.count() for shop in shops) if hasattr(shops.first(), 'listing_set') else 0,
        'active_shops': shops.filter(is_active=True).count(),
    }
    
    return render(request, 'admin/dashboard.html', context)


@login_required(login_url='login')
def admin_shops_view(request, username=None):
    """
    Admin shops management page.
    List all shops for the user with edit/delete options.
    """
    if username:
        target_user = get_object_or_404(User, username=username)
        if request.user != target_user and not request.user.is_superuser:
            messages.error(request, 'You do not have permission to view this page.')
            return redirect('admin_dashboard')
        user = target_user
    else:
        user = request.user
    
    shops = Shop.objects.filter(owner=user).order_by('-created_at')
    
    context = {
        'target_user': user,
        'shops': shops,
    }
    
    return render(request, 'admin/shops.html', context)


@login_required(login_url='login')
def admin_shop_detail_view(request, username=None, shop_id=None):
    """
    Admin shop detail page.
    Edit shop info, view listings, analytics.
    """
    if username:
        target_user = get_object_or_404(User, username=username)
        if request.user != target_user and not request.user.is_superuser:
            messages.error(request, 'You do not have permission to view this shop.')
            return redirect('admin_dashboard')
    else:
        target_user = request.user
    
    shop = get_object_or_404(Shop, id=shop_id, owner=target_user)
    
    # Get shop listings
    listings = shop.listing_set.all() if hasattr(shop, 'listing_set') else []
    
    context = {
        'shop': shop,
        'target_user': target_user,
        'listings': listings,
        'listing_count': len(listings),
    }
    
    return render(request, 'admin/shop_detail.html', context)
