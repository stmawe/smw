"""
Admin subdomain views for https://admin.smw.pgwiz.cloud/
Provides admin dashboard and shop management for sellers.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.urls import reverse
from .models import User
from mydak.models import Shop


def admin_login_required(function):
    """
    Custom login required decorator for admin subdomain.
    Redirects to admin login if not authenticated.
    """
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            # Verify user is staff/admin
            if request.user.is_staff or request.user.is_superuser:
                return function(request, *args, **kwargs)
            else:
                messages.error(request, 'Only admin users can access this area.')
                return redirect('admin_login')
        # Redirect to admin login
        return redirect('admin_login')
    return wrapper


def admin_login_view(request):
    """
    Admin login page for admin.smw.pgwiz.cloud
    Only allows staff and superuser access
    """
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_dashboard_full')
        else:
            return redirect('admin_login')
    
    if request.method == 'POST':
        username_email = request.POST.get('username')
        password = request.POST.get('password')
        
        # authenticate() will use UsernameOrEmailBackend which supports both
        user = authenticate(request, username=username_email, password=password)
        
        if user is not None:
            # Check if user is admin/staff
            if user.is_staff or user.is_superuser:
                login(request, user)
                return redirect('admin_dashboard_full')
            else:
                messages.error(request, 'Only admin users can access this area.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'admin/login.html', {'title': 'Admin Login'})


@admin_login_required
def admin_dashboard_view(request, username=None):
    """
    Admin dashboard main page.
    Shows overview of shops, sales, analytics.
    
    Accessed from:
    - /dashboard/ on main site
    - / or /dashboard/ on admin.smw.pgwiz.cloud subdomain
    """
    # If accessing admin subdomain root, redirect to /dashboard/
    if getattr(request, 'is_admin_subdomain', False) and request.path == '/':
        from django.shortcuts import redirect
        return redirect('/dashboard/')
    
    # If username is specified, check if user has permission to view it
    if username:
        target_user = get_object_or_404(User, username=username)
        # Only allow viewing own dashboard unless superuser
        if request.user != target_user and not request.user.is_superuser:
            messages.error(request, 'You do not have permission to view this dashboard.')
            return redirect('admin_dashboard_full')
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


@admin_login_required
def admin_shops_view(request, username=None):
    """
    Admin shops management page.
    List all shops for the user with edit/delete options.
    """
    if username:
        target_user = get_object_or_404(User, username=username)
        if request.user != target_user and not request.user.is_superuser:
            messages.error(request, 'You do not have permission to view this page.')
            return redirect('admin_dashboard_full')
        user = target_user
    else:
        user = request.user
    
    shops = Shop.objects.filter(owner=user).order_by('-created_at')
    
    context = {
        'target_user': user,
        'shops': shops,
    }
    
    return render(request, 'admin/shops.html', context)


@admin_login_required
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
