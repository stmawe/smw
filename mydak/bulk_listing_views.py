"""Bulk listing management views."""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from mydak.models import Listing, Shop
from mydak.bulk_listing_forms import (
    BulkListingUploadForm,
    BulkListingValidator,
    BulkListingPreviewForm,
)


@login_required
@require_http_methods(['GET', 'POST'])
def bulk_listing_upload_view(request):
    """Handle bulk listing CSV upload."""
    user_shops = Shop.objects.filter(owner=request.user)
    
    if not user_shops.exists():
        messages.error(request, 'You must have at least one shop to upload listings')
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
        form = BulkListingUploadForm()
        return render(request, 'listings/bulk_upload.html', {
            'form': form,
            'shops': user_shops,
            'selected_shop': shop,
        })
    
    # POST request - process upload
    form = BulkListingUploadForm(request.POST, request.FILES)
    
    if not form.is_valid():
        return render(request, 'listings/bulk_upload.html', {
            'form': form,
            'shops': user_shops,
            'selected_shop': shop,
        }, status=400)
    
    try:
        rows = form.parse_csv()
    except Exception as e:
        messages.error(request, f'CSV parsing failed: {str(e)}')
        return render(request, 'listings/bulk_upload.html', {
            'form': form,
            'shops': user_shops,
            'selected_shop': shop,
        }, status=400)
    
    # Validate all rows
    preview_data = []
    errors = []
    
    for idx, row in enumerate(rows, start=1):
        row_errors = BulkListingValidator.validate_row(row, idx)
        if row_errors:
            errors.extend(row_errors)
        else:
            prepared = BulkListingValidator.prepare_listing_data(row)
            preview_data.append({
                'row': idx,
                'title': prepared['title'],
                'price': prepared['price'],
                'category': prepared['category'].name,
                'condition': prepared['condition'],
                'description': prepared['description'][:100] + '...' if prepared['description'] else '',
            })
    
    if errors:
        messages.error(request, f'Validation failed: {len(errors)} error(s)')
        for error in errors[:10]:  # Show first 10 errors
            messages.warning(request, error)
        return render(request, 'listings/bulk_upload.html', {
            'form': form,
            'shops': user_shops,
            'selected_shop': shop,
        }, status=400)
    
    # Store in session for preview
    request.session['bulk_preview'] = preview_data
    request.session['bulk_csv_data'] = rows
    request.session['bulk_shop_id'] = shop.id
    
    return redirect('shops:bulk_preview')


@login_required
@require_http_methods(['GET'])
def bulk_listing_preview_view(request):
    """Show preview of bulk upload before confirmation."""
    # Retrieve data from session
    preview_data = request.session.get('bulk_preview', [])
    shop_id = request.session.get('bulk_shop_id')
    
    if not preview_data or not shop_id:
        messages.error(request, 'No preview available. Please upload again')
        return redirect('shops:bulk_upload')
    
    try:
        shop = Shop.objects.get(id=shop_id, owner=request.user)
    except Shop.DoesNotExist:
        messages.error(request, 'Shop not found')
        return redirect('shops:list')
    
    return render(request, 'listings/bulk_preview.html', {
        'preview_data': preview_data,
        'total_count': len(preview_data),
        'shop': shop,
    })


@login_required
@require_http_methods(['POST'])
def bulk_listing_confirm_view(request):
    """Confirm and import bulk listings."""
    user_shops = Shop.objects.filter(owner=request.user)
    
    # Retrieve data from session
    preview_data = request.session.get('bulk_preview', [])
    csv_data = request.session.get('bulk_csv_data', [])
    shop_id = request.session.get('bulk_shop_id')
    
    if not preview_data or not csv_data or not shop_id:
        messages.error(request, 'Session expired. Please upload again')
        return redirect('shops:bulk_upload')
    
    try:
        shop = user_shops.get(id=shop_id)
    except Shop.DoesNotExist:
        messages.error(request, 'Shop not found')
        return redirect('shops:list')
    
    form = BulkListingPreviewForm(request.POST)
    
    if not form.is_valid():
        messages.error(request, 'Please confirm the import')
        return render(request, 'listings/bulk_preview.html', {
            'preview_data': preview_data,
            'total_count': len(preview_data),
            'shop': shop,
        }, status=400)
    
    # Import listings
    created_count = 0
    failed_count = 0
    
    for row in csv_data:
        try:
            prepared = BulkListingValidator.prepare_listing_data(row)
            Listing.objects.create(
                title=prepared['title'],
                price=prepared['price'],
                category=prepared['category'],
                condition=prepared['condition'],
                description=prepared['description'],
                seller=request.user,
                shop=shop,
                status='draft',
            )
            created_count += 1
        except Exception as e:
            failed_count += 1
    
    # Clean up session
    if 'bulk_preview' in request.session:
        del request.session['bulk_preview']
    if 'bulk_csv_data' in request.session:
        del request.session['bulk_csv_data']
    if 'bulk_shop_id' in request.session:
        del request.session['bulk_shop_id']
    
    if failed_count > 0:
        messages.warning(
            request,
            f'Imported {created_count} listing(s), but {failed_count} failed.'
        )
    else:
        messages.success(request, f'✅ All {created_count} listings imported successfully!')
    
    return redirect('shops:my_listings')


@login_required
@require_http_methods(['GET'])
def bulk_listing_cancel_view(request):
    """Cancel bulk upload."""
    # Clean up session
    if 'bulk_preview' in request.session:
        del request.session['bulk_preview']
    if 'bulk_csv_data' in request.session:
        del request.session['bulk_csv_data']
    if 'bulk_shop_id' in request.session:
        del request.session['bulk_shop_id']
    
    messages.info(request, 'Bulk upload cancelled')
    return redirect('mydak:seller_dashboard')
