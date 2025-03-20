from django import template

register = template.Library()

@register.filter
def get(dictionary, key):
    """Get a value from a dictionary using a key"""
    if not isinstance(dictionary, dict):
        return 0
    return dictionary.get(key, 0)

@register.filter
def sub(value, arg):
    """Subtract arg from value"""
    try:
        return float(value or 0) - float(arg or 0)
    except (ValueError, TypeError):
        return 0