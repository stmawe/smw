"""Theme management views."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .models import Theme, ShopTheme
from .engine import ThemeEngine


@login_required
@require_http_methods(["GET"])
def theme_list_view(request):
    """List available themes."""
    themes = Theme.objects.filter(is_active=True).order_by('-is_built_in', 'name')
    
    context = {
        'themes': themes,
    }
    
    return render(request, 'themes/theme_list.html', context)


@login_required
@require_http_methods(["POST"])
def theme_apply_view(request, theme_id):
    """Apply theme to current shop."""
    # This requires being on a tenant/shop
    if not hasattr(request, 'tenant') or not request.tenant:
        return JsonResponse({'status': 'error', 'message': 'Not in a shop context'}, status=400)
    
    theme = get_object_or_404(Theme, id=theme_id, is_active=True)
    shop = request.tenant
    
    # Get or create ShopTheme
    shop_theme, created = ShopTheme.objects.get_or_create(shop=shop)
    shop_theme.theme = theme
    shop_theme.enabled = True
    shop_theme.save()
    
    # Clear cache
    engine = ThemeEngine(shop)
    engine.clear_cache()
    
    messages.success(request, f'Theme "{theme.name}" applied successfully!')
    
    return JsonResponse({
        'status': 'success',
        'message': f'Theme applied: {theme.name}',
    })


@login_required
@require_http_methods(["POST"])
def theme_customize_view(request, shop_id):
    """
    Customize theme for a shop.
    Accepts JSON with custom CSS properties.
    """
    import json
    
    try:
        shop_theme = ShopTheme.objects.get(shop_id=shop_id)
    except ShopTheme.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Shop theme not found'}, status=404)
    
    try:
        data = json.loads(request.body)
        custom_overrides = data.get('custom_overrides', {})
        
        # Validate it's a dict of CSS properties
        if not isinstance(custom_overrides, dict):
            return JsonResponse({'status': 'error', 'message': 'Invalid overrides format'}, status=400)
        
        shop_theme.custom_overrides = custom_overrides
        shop_theme.save()
        
        # Clear cache
        engine = ThemeEngine(shop_theme.shop)
        engine.clear_cache()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Theme customized successfully',
            'css': shop_theme.get_css_string(),
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def theme_preview_view(request, theme_id):
    """Preview a theme."""
    theme = get_object_or_404(Theme, id=theme_id, is_active=True)
    
    engine = ThemeEngine()
    engine.theme = theme
    css = engine.get_css()
    
    context = {
        'theme': theme,
        'theme_css': css,
    }
    
    return render(request, 'themes/theme_preview.html', context)


@require_http_methods(["GET"])
def theme_css_view(request, shop_id=None):
    """
    Serve theme CSS as a static resource.
    Can be cached by browser.
    """
    if shop_id:
        try:
            from mydak.models import Shop
            shop = Shop.objects.get(id=shop_id)
            engine = ThemeEngine(shop)
        except Exception:
            return JsonResponse({'error': 'Shop not found'}, status=404)
    else:
        engine = ThemeEngine()
    
    css = engine.get_css()
    
    # Serve as CSS file
    return JsonResponse({
        'css': css
    }, safe=False)
