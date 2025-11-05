from django import template

register = template.Library()


@register.filter(name='ugx')
def ugx(value, decimals=2):
    """Format numeric values as UGX with thousand separators.
    
    Usage: 
    {{ amount|ugx }} -> UGX 1,234,567.00
    {{ amount|ugx:0 }} -> UGX 1,234,567
    """
    try:
        amount = float(value)
        if decimals == 0:
            return f"UGX {amount:,.0f}"
        else:
            return f"UGX {amount:,.{decimals}f}"
    except (TypeError, ValueError):
        if decimals == 0:
            return 'UGX 0'
        return 'UGX 0.00'


@register.simple_tag
def currency(value, decimals=2):
    """Format value as currency (defaults to UGX).
    
    Usage: {% currency amount %} or {% currency amount 0 %}
    """
    try:
        amount = float(value)
        if decimals == 0:
            return f"UGX {amount:,.0f}"
        else:
            return f"UGX {amount:,.{decimals}f}"
    except (TypeError, ValueError):
        if decimals == 0:
            return 'UGX 0'
        return 'UGX 0.00'









