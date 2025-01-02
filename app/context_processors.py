def constants(request):
    return {
        'SITE_NAME': 'Property Spotter',
        'SUPPORT_EMAIL': 'support@example.com',
        'USERDATA': request.session.get('userData', None),
	'TOKEN': request.session.get('access_token', None),
    }