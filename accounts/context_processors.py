from accounts.models import Region


def regions(request):
    """Provide all active regions to all templates"""
    return {
        'all_regions': Region.objects.filter(is_active=True).order_by('name')
    }


def currency_settings(request):
    """Provide currency settings to all templates"""
    return {
        'CURRENCY_CODE': 'UGX',
        'CURRENCY_SYMBOL': 'UGX',
    }

