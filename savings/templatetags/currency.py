from django import template

register = template.Library()


@register.filter(name='ugx')
def ugx(value):
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return 'UGX 0.00'
    return f"UGX {amount:,.2f}"










