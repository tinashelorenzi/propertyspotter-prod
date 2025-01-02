def constants(request):
    return {
        'SITE_NAME': 'Property Spotter',
        'SUPPORT_EMAIL': 'support@example.com',
        'USERDATA': request.session.get('userData', None),
    }