"""Context processor for theme injection."""

from apps.themes.engine import ThemeEngine


def theme_context(request):
    """
    Context processor that adds theme CSS and engine to template context.
    """
    context = {
        'theme_css': '',
        'theme_engine': None,
    }
    
    # Get shop from request
    shop = getattr(request, 'tenant', None) if hasattr(request, 'tenant') else None
    
    if shop:
        engine = ThemeEngine(shop)
        context['theme_engine'] = engine
        context['theme_css'] = engine.get_css()
    
    return context
