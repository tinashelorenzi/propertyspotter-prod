from dotenv import load_dotenv
import os

load_dotenv()

def constants(request):
    # Get user data from session
    user_data = request.session.get('userData', None)
    
    # Initialize the context dictionary with basic constants
    context = {
        'SITE_NAME': 'Property Spotter',
        'SUPPORT_EMAIL': 'support@example.com',
        'USERDATA': user_data,
        'TOKEN': request.session.get('access_token', None),
        'DEPLOYMENT_MODE': os.getenv('DEPLOYMENT_MODE'),
    }
    
    # Add agency data only if user is an Agency Admin
    if user_data and user_data.get('role') == 'Agency_Admin':
        context['AGENCYDATA'] = request.session.get('agencyData', None)
    
    return context