"""Shop management views."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db import transaction
from .models import Shop
from .forms import ShopCreationForm, ShopEditForm
from apps.themes.models import ShopTheme
from apps.themes.builtin_themes import create_built_in_themes


@login_required
@require_http_methods(["GET", "POST"])
def shop_create_view(request):
    """
    Create a new shop (step 1 of wizard).
    """
    if request.method == 'POST':
        form = ShopCreationForm(request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create shop
                    shop = form.save(commit=False)
                    shop.owner = request.user
                    shop.is_active = True
                    shop.save()
                    
                    # Ensure built-in themes exist
                    create_built_in_themes()
                    
                    # Create default theme config for shop
                    default_theme = None
                    try:
                        from apps.themes.models import Theme
                        default_theme = Theme.objects.get(name='light', is_built_in=True)
                    except Exception:
                        pass
                    
                    ShopTheme.objects.get_or_create(
                        shop=shop,
                        defaults={'theme': default_theme, 'enabled': True}
                    )
                    
                    messages.success(request, f'Shop "{shop.name}" created successfully!')
                    return redirect('shops:detail', shop_id=shop.id)
            
            except Exception as e:
                messages.error(request, f'Error creating shop: {str(e)}')
                return redirect('shops:create')
    else:
        form = ShopCreationForm()
    
    context = {'form': form}
    return render(request, 'shops/shop_create.html', context)


@login_required
@require_http_methods(["GET"])
def shop_detail_view(request, shop_id):
    """View shop details and management."""
    shop = get_object_or_404(Shop, id=shop_id)
    
    # Only shop owner can view
    if shop.owner != request.user:
        messages.error(request, 'You do not have permission to view this shop.')
        return redirect('/')
    
    context = {
        'shop': shop,
        'shop_theme': getattr(shop, 'theme_config', None),
    }
    
    return render(request, 'shops/shop_detail.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def shop_edit_view(request, shop_id):
    """Edit shop details."""
    shop = get_object_or_404(Shop, id=shop_id)
    
    # Only shop owner can edit
    if shop.owner != request.user:
        messages.error(request, 'You do not have permission to edit this shop.')
        return redirect('/')
    
    if request.method == 'POST':
        form = ShopEditForm(request.POST, request.FILES, instance=shop)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Shop updated successfully!')
            return redirect('shops:detail', shop_id=shop.id)
    else:
        form = ShopEditForm(instance=shop)
    
    context = {
        'form': form,
        'shop': shop,
    }
    
    return render(request, 'shops/shop_edit.html', context)


@login_required
@require_http_methods(["GET"])
def shop_list_view(request):
    """List all shops owned by user."""
    shops = Shop.objects.filter(owner=request.user).order_by('-created_at')
    
    context = {
        'shops': shops,
    }
    
    return render(request, 'shops/shop_list.html', context)


@login_required
@require_http_methods(["POST"])
def shop_deactivate_view(request, shop_id):
    """Deactivate a shop."""
    shop = get_object_or_404(Shop, id=shop_id)
    
    if shop.owner != request.user:
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    
    shop.is_active = False
    shop.save()
    
    messages.success(request, f'Shop "{shop.name}" deactivated.')
    return redirect('shops:list')


@login_required
@require_http_methods(["POST"])
def shop_reactivate_view(request, shop_id):
    """Reactivate a shop."""
    shop = get_object_or_404(Shop, id=shop_id)
    
    if shop.owner != request.user:
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    
    shop.is_active = True
    shop.save()
    
    messages.success(request, f'Shop "{shop.name}" reactivated.')
    return redirect('shops:list')


# ============================================================
# SHOP SUBDOMAIN VIEWS
# For displaying shops when accessed via subdomain
# ============================================================

def shop_subdomain_view(request):
    """
    Shop homepage when accessed via subdomain.
    Extract shop from subdomain and display storefront.
    """
    # Get subdomain from request
    host = request.get_host().split(':')[0]  # Remove port if present
    parts = host.split('.')
    
    # Handle subdomains
    if len(parts) > 3:  # e.g., shopname.smw.pgwiz.cloud or username.smw.pgwiz.cloud
        shop_identifier = parts[0]  # Get the shop/username part
        
        # Try to find shop by name or owner username
        try:
            shop = Shop.objects.get(name__iexact=shop_identifier)
        except Shop.DoesNotExist:
            try:
                # Try to find by owner username
                from django.contrib.auth import get_user_model
                User = get_user_model()
                owner = User.objects.get(username=shop_identifier)
                # If multiple shops, show shop list for this user
                shops = Shop.objects.filter(owner=owner, is_active=True)
                if shops.count() == 1:
                    shop = shops.first()
                elif shops.count() > 1:
                    return render(request, 'shop_subdomain_list.html', {
                        'owner': owner,
                        'shops': shops,
                    })
                else:
                    return render(request, '404.html', {'message': 'Shop not found'}, status=404)
            except User.DoesNotExist:
                return render(request, '404.html', {'message': 'Shop not found'}, status=404)
        
        if not shop.is_active:
            return render(request, '404.html', {'message': 'Shop is not active'}, status=404)
        
        # Get shop listings
        listings = shop.listing_set.all() if hasattr(shop, 'listing_set') else []
        
        context = {
            'shop': shop,
            'listings': listings,
            'listing_count': len(listings),
        }
        return render(request, 'shop_storefront.html', context)
    
    return render(request, '404.html', {'message': 'Invalid shop URL'}, status=404)


def shop_products_view(request):
    """Shop products/listings page."""
    # Get subdomain
    host = request.get_host().split(':')[0]
    parts = host.split('.')
    
    if len(parts) > 3:
        shop_identifier = parts[0]
        try:
            shop = Shop.objects.get(name__iexact=shop_identifier)
        except Shop.DoesNotExist:
            return render(request, '404.html', status=404)
        
        listings = shop.listing_set.all() if hasattr(shop, 'listing_set') else []
        context = {
            'shop': shop,
            'listings': listings,
        }
        return render(request, 'shop_products.html', context)
    
    return render(request, '404.html', status=404)


def shop_product_detail_view(request, product_id):
    """Individual product detail page on shop subdomain."""
    # Get shop from subdomain
    host = request.get_host().split(':')[0]
    parts = host.split('.')
    
    if len(parts) > 3:
        shop_identifier = parts[0]
        try:
            shop = Shop.objects.get(name__iexact=shop_identifier)
        except Shop.DoesNotExist:
            return render(request, '404.html', status=404)
        
        # Get the listing/product
        try:
            listing = shop.listing_set.get(id=product_id) if hasattr(shop, 'listing_set') else None
            if not listing:
                return render(request, '404.html', status=404)
            
            context = {
                'shop': shop,
                'listing': listing,
            }
            return render(request, 'listing_detail_subdomain.html', context)
        except:
            return render(request, '404.html', status=404)
    
    return render(request, '404.html', status=404)


def shop_about_view(request):
    """Shop about page."""
    host = request.get_host().split(':')[0]
    parts = host.split('.')
    
    if len(parts) > 3:
        shop_identifier = parts[0]
        try:
            shop = Shop.objects.get(name__iexact=shop_identifier)
        except Shop.DoesNotExist:
            return render(request, '404.html', status=404)
        
        context = {
            'shop': shop,
        }
        return render(request, 'shop_about_subdomain.html', context)
    
    return render(request, '404.html', status=404)
