"""Listing management views."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db.models import Q
from mydak.models import Listing, Shop
from mydak.listing_forms import ListingCreationForm, ListingEditForm, ListingSearchForm


@login_required
@require_http_methods(["GET", "POST"])
def listing_create_view(request, shop_id):
    """Create a new listing for a shop."""
    shop = get_object_or_404(Shop, id=shop_id, owner=request.user)
    
    if request.method == 'POST':
        form = ListingCreationForm(request.POST, request.FILES)
        
        if form.is_valid():
            listing = form.save(commit=False)
            listing.shop = shop
            listing.seller = request.user
            listing.status = 'draft'
            listing.save()
            
            messages.success(request, f'Listing "{listing.title}" created successfully!')
            return redirect('listings:detail', listing_id=listing.id)
    else:
        form = ListingCreationForm()
    
    context = {'form': form, 'shop': shop}
    return render(request, 'listings/listing_create.html', context)


@login_required
@require_http_methods(["GET"])
def listing_detail_view(request, listing_id):
    """View listing details."""
    listing = get_object_or_404(Listing, id=listing_id, status__in=['active', 'draft', 'sold'])
    
    # Increment view count
    if request.user != listing.seller:
        listing.views += 1
        listing.save()
    
    context = {'listing': listing}
    return render(request, 'listings/listing_detail.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def listing_edit_view(request, listing_id):
    """Edit a listing."""
    listing = get_object_or_404(Listing, id=listing_id, seller=request.user)
    
    if request.method == 'POST':
        form = ListingEditForm(request.POST, request.FILES, instance=listing)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Listing updated successfully!')
            return redirect('listings:detail', listing_id=listing.id)
    else:
        form = ListingEditForm(instance=listing)
    
    context = {'form': form, 'listing': listing}
    return render(request, 'listings/listing_edit.html', context)


@login_required
@require_http_methods(["POST"])
def listing_delete_view(request, listing_id):
    """Delete a listing."""
    listing = get_object_or_404(Listing, id=listing_id, seller=request.user)
    shop_id = listing.shop.id
    
    listing.status = 'hidden'
    listing.save()
    
    messages.success(request, 'Listing deleted successfully!')
    return redirect('shops:detail', shop_id=shop_id)


@login_required
@require_http_methods(["POST"])
def listing_publish_view(request, listing_id):
    """Publish a draft listing."""
    listing = get_object_or_404(Listing, id=listing_id, seller=request.user, status='draft')
    
    listing.status = 'active'
    listing.save()
    
    messages.success(request, 'Listing published successfully!')
    return redirect('listings:detail', listing_id=listing.id)


@login_required
@require_http_methods(["POST"])
def listing_mark_sold_view(request, listing_id):
    """Mark a listing as sold."""
    listing = get_object_or_404(Listing, id=listing_id, seller=request.user, status='active')
    
    listing.status = 'sold'
    listing.save()
    
    messages.success(request, 'Listing marked as sold!')
    return redirect('listings:detail', listing_id=listing.id)


@require_http_methods(["GET"])
def listing_search_view(request):
    """Search and filter listings."""
    form = ListingSearchForm(request.GET)
    listings = Listing.objects.filter(status='active').order_by('-created_at')
    
    if form.is_valid():
        # Search query
        query = form.cleaned_data.get('query')
        if query:
            listings = listings.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query)
            )
        
        # Category filter
        category = form.cleaned_data.get('category')
        if category:
            listings = listings.filter(category=category)
        
        # Condition filter
        condition = form.cleaned_data.get('condition')
        if condition:
            listings = listings.filter(condition=condition)
        
        # Price range filter
        price_min = form.cleaned_data.get('price_min')
        if price_min is not None:
            listings = listings.filter(price__gte=price_min)
        
        price_max = form.cleaned_data.get('price_max')
        if price_max is not None:
            listings = listings.filter(price__lte=price_max)
        
        # Sorting
        sort_by = form.cleaned_data.get('sort_by')
        if sort_by == 'price_low':
            listings = listings.order_by('price')
        elif sort_by == 'price_high':
            listings = listings.order_by('-price')
        elif sort_by == 'popular':
            listings = listings.order_by('-views')
    
    context = {
        'form': form,
        'listings': listings[:50],  # Paginate in future
        'total_count': listings.count(),
    }
    
    return render(request, 'listings/listing_search.html', context)


@login_required
@require_http_methods(["GET"])
def my_listings_view(request):
    """View user's own listings."""
    listings = Listing.objects.filter(seller=request.user).order_by('-created_at')
    
    context = {
        'listings': listings,
        'draft_count': listings.filter(status='draft').count(),
        'active_count': listings.filter(status='active').count(),
        'sold_count': listings.filter(status='sold').count(),
    }
    
    return render(request, 'listings/my_listings.html', context)
