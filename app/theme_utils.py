"""
Context processor and utility functions for theme system.
Automatically injects theme CSS into all templates.
"""

from django.core.cache import cache
from app.models import Theme, PageThemeAssignment


def get_active_theme():
    """
    Get the currently active theme, with caching.
    """
    theme = cache.get('active_theme_object')
    if theme is None:
        try:
            theme = Theme.objects.get(is_active=True)
            cache.set('active_theme_object', theme, 3600)  # Cache for 1 hour
        except Theme.DoesNotExist:
            return None
    return theme


def get_theme_for_page(page_type):
    """
    Get the appropriate theme for a specific page type.
    Falls back to global theme if no page-specific assignment.
    
    Args:
        page_type: One of the PAGE_TYPES from PageThemeAssignment model
    
    Returns:
        Theme object or None
    """
    try:
        assignment = PageThemeAssignment.objects.get(page_type=page_type)
        if assignment.override_enabled and assignment.theme:
            return assignment.theme
    except PageThemeAssignment.DoesNotExist:
        pass
    
    # Fall back to global theme
    return get_active_theme()


def generate_theme_css(theme_obj):
    """
    Generate CSS for a theme object. Cached.
    """
    if theme_obj is None:
        return ""
    
    cache_key = f'theme_css_{theme_obj.id}'
    css = cache.get(cache_key)
    if css is None:
        css = theme_obj.generate_css()
        cache.set(cache_key, css, 3600)  # Cache for 1 hour
    return css


def theme_context_processor(request):
    """
    Context processor that adds theme CSS to every template.
    Add to TEMPLATES[0]['OPTIONS']['context_processors'] in settings.py
    
    Usage in templates:
        {{ theme_css|safe }}  <!-- Injects theme CSS -->
        {{ theme_js|safe }}   <!-- For future JS theme API -->
    """
    
    # Get page type from view kwargs if available
    page_type = request.resolver_match.kwargs.get('page_type', 'homepage')
    
    # Get appropriate theme
    theme = get_theme_for_page(page_type)
    
    # Generate CSS
    theme_css = generate_theme_css(theme)
    
    return {
        'theme_css': theme_css,
        'current_theme': theme,
    }
