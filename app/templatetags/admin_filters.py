from django import template

register = template.Library()

@register.filter
def dict_lookup(dictionary, key):
    """
    Access dictionary values by key in templates.
    Usage: {{ row|dict_lookup:"username" }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return ''

@register.filter
def field_or_attr(obj, attr_name):
    """
    Get either a dictionary value or object attribute.
    Usage: {{ obj|field_or_attr:"email" }}
    """
    if isinstance(obj, dict):
        return obj.get(attr_name, '')
    return getattr(obj, attr_name, '')

@register.filter
def format_currency(value):
    """
    Format value as currency.
    Usage: {{ price|format_currency }}
    """
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return value

@register.filter
def status_class(status):
    """
    Return Bootstrap class for status.
    Usage: <span class="{{ status|status_class }}">{{ status }}</span>
    """
    status_map = {
        'active': 'badge bg-success',
        'inactive': 'badge bg-secondary',
        'pending': 'badge bg-warning text-dark',
        'approved': 'badge bg-success',
        'rejected': 'badge bg-danger',
        'warning': 'badge bg-warning text-dark',
        'error': 'badge bg-danger',
        'success': 'badge bg-success',
    }
    return status_map.get(str(status).lower(), 'badge bg-primary')
