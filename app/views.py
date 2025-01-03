from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from .decorators import securedRoute
from dateutil.relativedelta import relativedelta
from datetime import datetime
import json, requests
CustomUser = get_user_model()
# Create your views here.

def index(request):
	return render(request, 'index.html')

def login_view(request):
    return render(request, 'login.html')

def dashboard(request):
    base_url = request.build_absolute_uri('/')[:-1]
    user_id = request.session.get('userData', {}).get('id')

    # Fetch data
    leads_response = requests.get(f'{base_url}/api/leads/by-spotter/{user_id}/', 
                        headers={'Authorization': f'Bearer {request.session.get("access_token")}'})
    commissions_response = requests.get(f'{base_url}/api/commissions/',
                             headers={'Authorization': f'Bearer {request.session.get("access_token")}'})

    leads = leads_response.json() if leads_response.ok else []
    commissions = commissions_response.json() if commissions_response.ok else []

    # Process leads data
    total_leads = len(leads)
    active_leads = sum(1 for l in leads if l.get('status') not in ['Commission Paid', 'Unsuccessful'])
    completed_leads = sum(1 for l in leads if l.get('status') == 'Commission Paid')
    
    # Recent leads processing
    recent_leads = []
    for lead in leads[:5]:  # Last 5 leads
        recent_leads.append({
            'property_address': lead['property']['address'],
            'status': lead['status'],
            'created_at': lead['created_at'],
            'value': lead['property']['price'],
            'status_color': get_status_color(lead['status'])
        })

    # Calculate revenue from last 6 months
    revenue_data = {
        'months': [],
        'values': []
    }
    for i in range(5, -1, -1):
        month = (datetime.now() - relativedelta(months=i)).strftime('%b')
        revenue_data['months'].append(month)
        revenue_data['values'].append(0)  # Initialize with 0

    for comm in commissions:
        if comm.get('spotter') == user_id and comm.get('status') == 'Paid':
            month = datetime.strptime(comm['paid_at'], '%Y-%m-%dT%H:%M:%SZ').strftime('%b')
            if month in revenue_data['months']:
                idx = revenue_data['months'].index(month)
                revenue_data['values'][idx] += float(comm.get('amount', 0))

    # Status distribution for pie chart
    status_data = {
        'labels': [],
        'values': []
    }
    status_counts = {}
    for lead in leads:
        status = lead.get('status', 'Unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    status_data['labels'] = list(status_counts.keys())
    status_data['values'] = list(status_counts.values())

    context = {
        'total_leads': total_leads,
        'active_leads': active_leads,
        'revenue': sum(revenue_data['values']),
        'conversion_rate': round((completed_leads / total_leads * 100) if total_leads > 0 else 0, 1),
        'recent_leads': recent_leads,
        'revenue_data': revenue_data,
        'status_data': status_data
    }
    
    return render(request, 'spotter_dashboard.html', context)

def get_status_color(status):
    colors = {
        'New Submission': 'primary',
        'Commission Paid': 'success',
        'Unsuccessful': 'danger',
        'Listed': 'info',
        'Pending Mandate': 'warning'
    }
    return colors.get(status, 'secondary')

@securedRoute
def myLeads(request):
    return render(request, 'spotter_leads.html')

@securedRoute
def myHistory(request):
    return render(request, 'spotter_history.html')

@securedRoute
def myProfile(request):
    return render(request, 'spotter_profile.html')

@securedRoute
def newLead(request):
    return render(request, 'new_lead.html')

@csrf_exempt
def sessionSave(request):
    print(json.loads(request.body))
    if request.method == 'POST':
        try:
            # Parse the request body
            data = json.loads(request.body)
            access_token = data.get('accessToken')
            refresh_token = data.get('refreshToken')

            # Check if tokens are provided
            if not access_token or not refresh_token:
                return JsonResponse({'error': 'Tokens are required'}, status=400)

            # Initialize the JWT authentication class
            jwt_auth = JWTAuthentication()

            # Validate the access token
            try:
                validated_token = jwt_auth.get_validated_token(access_token)
                user = jwt_auth.get_user(validated_token)
            except TokenError as e:
                return JsonResponse({'error': f'Token error: {str(e)}'}, status=401)
            except InvalidToken as e:
                return JsonResponse({'error': 'Invalid token'}, status=401)

            # Save user data and tokens in the session
            request.session['user_id'] = str(user.id)  # Convert UUID to string if necessary
            request.session['role'] = user.role
            request.session['access_token'] = access_token
            request.session['refresh_token'] = refresh_token
            request.session['loggedIn'] = True
            request.session['userData'] = data.get('userData')

            return JsonResponse({'message': 'Session saved successfully'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

def token(request):
    print("Token: "+request.session.get('access_token'))
    return JsonResponse({'token': request.session.get('access_token')})

def logout(request):
    request.session.flush()
    return redirect('/')