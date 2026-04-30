"""Listing template views."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from mydak.models import ListingTemplate, Shop
from mydak.template_forms import ListingTemplateForm, CreateListingFromTemplateForm


@login_required
@require_http_methods(['GET', 'POST'])
def template_create_view(request):
    """Create a new listing template."""
    user_shops = Shop.objects.filter(owner=request.user)
    
    if not user_shops.exists():
        messages.error(request, 'You must have at least one shop to create templates')
        return redirect('shops:list')
    
    # Get selected shop (from GET param or first shop)
    shop_id = request.GET.get('shop_id') or request.POST.get('shop_id')
    if shop_id:
        try:
            shop = user_shops.get(id=shop_id)
        except Shop.DoesNotExist:
            messages.error(request, 'Shop not found')
            return redirect('shops:list')
    else:
        shop = user_shops.first()
    
    if request.method == 'GET':
        form = ListingTemplateForm()
        return render(request, 'listings/template_create.html', {
            'form': form,
            'shops': user_shops,
            'selected_shop': shop,
        })
    
    # POST request - create template
    form = ListingTemplateForm(request.POST)
    
    if not form.is_valid():
        return render(request, 'listings/template_create.html', {
            'form': form,
            'shops': user_shops,
            'selected_shop': shop,
        }, status=400)
    
    template = form.save(commit=False)
    template.seller = request.user
    template.shop = shop
    template.save()
    
    messages.success(request, f'✅ Template "{template.name}" created successfully!')
    return redirect('template_list')


@login_required
@require_http_methods(['GET'])
def template_list_view(request):
    """List seller's listing templates."""
    shop_id = request.GET.get('shop_id')
    user_shops = Shop.objects.filter(owner=request.user)
    
    if shop_id:
        try:
            shop = user_shops.get(id=shop_id)
        except Shop.DoesNotExist:
            messages.error(request, 'Shop not found')
            return redirect('shops:list')
        templates = ListingTemplate.objects.filter(
            seller=request.user,
            shop=shop,
            is_active=True
        ).select_related('category')
    else:
        templates = ListingTemplate.objects.filter(
            seller=request.user,
            is_active=True
        ).select_related('category', 'shop')
        shop = None
    
    return render(request, 'listings/template_list.html', {
        'templates': templates,
        'shops': user_shops,
        'selected_shop': shop,
    })


@login_required
@require_http_methods(['GET', 'POST'])
def template_edit_view(request, template_id):
    """Edit a listing template."""
    template = get_object_or_404(ListingTemplate, id=template_id, seller=request.user)
    
    if request.method == 'GET':
        form = ListingTemplateForm(instance=template)
        return render(request, 'listings/template_edit.html', {
            'form': form,
            'template': template,
        })
    
    # POST request - update template
    form = ListingTemplateForm(request.POST, instance=template)
    
    if not form.is_valid():
        return render(request, 'listings/template_edit.html', {
            'form': form,
            'template': template,
        }, status=400)
    
    template = form.save()
    messages.success(request, f'✅ Template "{template.name}" updated successfully!')
    return redirect('template_list')


@login_required
@require_http_methods(['POST'])
def template_delete_view(request, template_id):
    """Delete a listing template (soft delete)."""
    template = get_object_or_404(ListingTemplate, id=template_id, seller=request.user)
    
    template.is_active = False
    template.save()
    
    messages.success(request, f'✅ Template "{template.name}" deleted successfully!')
    return redirect('template_list')


@login_required
@require_http_methods(['GET', 'POST'])
def create_listing_from_template_view(request, template_id):
    """Create a listing using a template."""
    template = get_object_or_404(
        ListingTemplate,
        id=template_id,
        seller=request.user,
        is_active=True
    )
    
    if request.method == 'GET':
        form = CreateListingFromTemplateForm(initial={'template_id': template_id})
        return render(request, 'listings/create_from_template.html', {
            'form': form,
            'template': template,
        })
    
    # POST request - create listing from template
    form = CreateListingFromTemplateForm(request.POST)
    
    if not form.is_valid():
        return render(request, 'listings/create_from_template.html', {
            'form': form,
            'template': template,
        }, status=400)
    
    # Create listing using template
    listing = template.create_listing_from_template(
        title=form.cleaned_data['title'],
        price=form.cleaned_data['price']
    )
    
    messages.success(request, f'✅ Listing "{listing.title}" created from template!')
    return redirect('shops:detail', listing_id=listing.id)


@login_required
@require_http_methods(['GET'])
def clone_listing_as_template_view(request, listing_id):
    """Clone an existing listing as a template."""
    from mydak.models import Listing
    
    listing = get_object_or_404(Listing, id=listing_id, seller=request.user)
    
    # Create template from listing
    template_name = f'{listing.title} Template'
    
    # Check if template with this name already exists
    counter = 1
    original_name = template_name
    while ListingTemplate.objects.filter(shop=listing.shop, name=template_name).exists():
        counter += 1
        template_name = f'{original_name} ({counter})'
    
    template = ListingTemplate.objects.create(
        seller=request.user,
        shop=listing.shop,
        name=template_name,
        category=listing.category,
        condition=listing.condition,
        description=listing.description,
    )
    
    messages.success(request, f'✅ Listing cloned as template "{template.name}"!')
    return redirect('template_list')
