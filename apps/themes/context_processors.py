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
    
    # Get shop from request - for now, don't use tenant as it's a Client, not Shop
    # TODO: Link Client to Shop once Shop relationship is established
    shop = None
    
    if shop:
        try:
            engine = ThemeEngine(shop)
            context['theme_engine'] = engine
            context['theme_css'] = engine.get_css()
        except Exception:
            # If theme loading fails, continue without theme
            pass
    
    return context
