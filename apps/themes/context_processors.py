"""Context processor for theme injection."""

from apps.themes.engine import ThemeEngine
from mydak.models import Shop


def _resolve_shop(request):
    """Resolve the current shop for theme rendering if one exists."""
    shop = getattr(request, 'shop', None)
    if shop and getattr(shop, 'pk', None):
        return shop

    tenant = getattr(request, 'tenant', None)
    if tenant and getattr(tenant, 'tenant_type', None) == 'shop':
        tenant_name = getattr(tenant, 'name', '')
        if tenant_name:
            resolved = Shop.objects.filter(name__iexact=tenant_name, is_active=True).first()
            if resolved:
                return resolved

    host = request.get_host().split(':')[0]
    if host.startswith('admin.'):
        return None

    parts = host.split('.')
    if len(parts) < 3:
        return None

    subdomain = parts[0]
    if not subdomain or subdomain in {'www', 'admin'}:
        return None

    shop = Shop.objects.filter(domain__iexact=subdomain, is_active=True).first()
    if shop:
        return shop

    return Shop.objects.filter(name__iexact=subdomain, is_active=True).first()


def theme_context(request):
    """
    Context processor that adds theme CSS and engine to template context.
    """
    context = {
        'theme_css': '',
        'theme_engine': None,
    }
    
    shop = _resolve_shop(request)

    if shop:
        engine = ThemeEngine(shop)
        context['theme_engine'] = engine
        context['theme_css'] = engine.get_css()

    return context
