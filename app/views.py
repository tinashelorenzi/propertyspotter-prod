from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import csrf_protect
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from .decorators import securedRoute
from dateutil.relativedelta import relativedelta
from datetime import datetime
from django.db.models import Q, F
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
import json, requests
from collections import defaultdict
CustomUser = get_user_model()
# Create your views here.

def index(request):
	return render(request, 'index.html')

def login_view(request):
    return render(request, 'login.html')

@csrf_exempt
def spotter_register(request):
    return render(request, 'spotter_registration.html')

@securedRoute
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
    
    #render the relevent template based on user role
    print("Role: " + request.session.get('userData', {}).get('role'))
    if request.session.get('userData', {}).get('role') == 'Spotter':
        print("Rendering spotter dashboard")
        return render(request, 'spotter_dashboard.html', context)
    elif request.session.get('userData', {}).get('role') == 'Agency_Admin':
        print("Rendering agency dashboard")
        #Add the session login for the agencyData here
        agency_response = requests.get(f'{base_url}/api/agency/get-agency-by-admin/{user_id}/',headers={'Authorization': f'Bearer {request.session.get("access_token")}'})
        if agency_response.ok:
            agency_data = agency_response.json()
            request.session['agencyData'] = agency_data
            print("Agency data stored in session:", agency_data)
        else:
            print("Failed to fetch agency data:", agency_response.status_code, agency_response.text)
        return redirect('/agency')
    elif request.session.get('userData', {}).get('role') == 'Agent':
        return redirect('/agent/dashboard')
    else:
        print("Rendering admin dashboard")
        return render(request, 'admin_dashboard.html', context)

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

# Agency Dashboard Routes
@securedRoute
def agency_dashboard(request):
    base_url = request.build_absolute_uri('/')[:-1]
    access_token = request.session.get('access_token')
    agency_data = request.session.get('agencyData')

    if not agency_data:
        return redirect('login')

    headers = {'Authorization': f'Bearer {access_token}'}

    try:
        # Fetch all leads for the agency
        leads_response = requests.get(
            f'{base_url}/api/leads/by-agency/{agency_data["id"]}/',
            headers=headers
        )
        leads = leads_response.json() if leads_response.ok else []

        # Calculate total sales (sum of all completed leads' property values)
        total_sales = sum(
            float(lead['property']['price']) 
            for lead in leads 
            if lead['status'] == 'Commission Paid' and lead['property'].get('price')
        )

        # Count active leads (not completed or unsuccessful)
        active_leads_count = sum(
            1 for lead in leads 
            if lead['status'] not in ['Commission Paid', 'Unsuccessful', 'Cancelled']
        )

        # Count new lead submissions
        new_leads_count = sum(
            1 for lead in leads 
            if lead['status'] == 'New_Submission'
        )

        # Get recent leads (last 5) and prepare them for display
        recent_leads = sorted(
            leads, 
            key=lambda x: x['created_at'], 
            reverse=True
        )[:5]

        # Calculate monthly stats for charts
        now = datetime.now()
        monthly_sales = defaultdict(float)
        monthly_leads = defaultdict(lambda: {'new': 0, 'converted': 0})

        # Process last 6 months of data
        for i in range(5, -1, -1):  # Going backward from 5 to 0
            month = (now - relativedelta(months=i)).strftime('%b')
            monthly_sales[month] = 0
            monthly_leads[month] = {'new': 0, 'converted': 0}

        # Calculate monthly sales and leads data
        for lead in leads:
            created_date = datetime.strptime(
                lead['created_at'].split('.')[0], 
                '%Y-%m-%dT%H:%M:%S'
            )
            month = created_date.strftime('%b')

            # Only process data from the last 6 months
            if month in monthly_sales:
                if lead['status'] == 'Commission Paid':
                    try:
                        monthly_sales[month] += float(lead['property']['price'])
                    except (KeyError, ValueError, TypeError):
                        continue

                if lead['status'] == 'New_Submission':
                    monthly_leads[month]['new'] += 1
                elif lead['status'] == 'Commission Paid':
                    monthly_leads[month]['converted'] += 1

        # Convert dictionaries to lists for the charts
        sales_chart_data = {
            'labels': list(monthly_sales.keys()),
            'values': list(monthly_sales.values())
        }

        leads_chart_data = {
            'labels': list(monthly_leads.keys()),
            'new_leads': [data['new'] for data in monthly_leads.values()],
            'converted_leads': [data['converted'] for data in monthly_leads.values()]
        }

        # Calculate trends
        current_month = now.strftime('%b')
        last_month = (now - relativedelta(months=1)).strftime('%b')
        
        sales_trend = calculate_trend(
            monthly_sales[current_month],
            monthly_sales[last_month]
        )
        
        leads_trend = calculate_trend(
            monthly_leads[current_month]['new'],
            monthly_leads[last_month]['new']
        )

        # Prepare the context
        context = {
            'agency': agency_data,
            'total_sales': total_sales,
            'active_leads_count': active_leads_count,
            'new_leads_count': new_leads_count,
            'recent_leads': recent_leads,
            'sales_chart_data': sales_chart_data,
            'leads_chart_data': leads_chart_data,
            'sales_trend': sales_trend,
            'leads_trend': leads_trend
        }

        return render(request, 'agency_dashboard.html', context)

    except Exception as e:
        print(f"Error in agency dashboard: {str(e)}")
        return redirect('login')

def calculate_trend(current_value, previous_value):
    """Calculate percentage change between two values"""
    if previous_value == 0:
        return 0
    return ((current_value - previous_value) / previous_value) * 100

@securedRoute
def agency_agents(request):
    base_url = request.build_absolute_uri('/')[:-1]
    access_token = request.session.get('access_token')
    agency_data = request.session.get('agencyData')

    if not agency_data:
        return redirect('login')

    headers = {'Authorization': f'Bearer {access_token}'}

    try:
        # First get all agents for this agency using our agency API
        agents_response = requests.get(
            f'{base_url}/api/agency/agents/{agency_data["id"]}/',
            headers=headers
        )
        
        if agents_response.ok:
            basic_agents = agents_response.json()
            
            # Now fetch detailed information for each agent
            agents_details = []
            for agent in basic_agents:
                # Get detailed user information
                user_response = requests.get(
                    f'{base_url}/api/users/{agent["id"]}/',
                    headers=headers
                )
                
                if user_response.ok:
                    agent_details = user_response.json()
                    # Add properties sold count from our original data
                    agent_details['properties_sold'] = agent.get('properties_sold', 0)
                    agents_details.append(agent_details)
                else:
                    print(f"Error fetching user details for {agent['id']}: {user_response.status_code}")
            
            context = {
                'agency': agency_data,
                'agents': agents_details
            }
            
            return render(request, 'agency_agents.html', context)
        else:
            print(f"Error fetching agents: {agents_response.status_code}")
            return render(request, 'agency_agents.html', {'agency': agency_data, 'agents': []})

    except Exception as e:
        print(f"Error in agents view: {str(e)}")
        return redirect('login')

@securedRoute
def agency_leads(request):
    base_url = request.build_absolute_uri('/')[:-1]
    access_token = request.session.get('access_token')
    agency_data = request.session.get('agencyData')

    if not agency_data:
        return redirect('login')

    headers = {'Authorization': f'Bearer {access_token}'}

    try:
        # Fetch all leads for the agency
        leads_response = requests.get(
            f'{base_url}/api/leads/by-agency/{agency_data["id"]}/',
            headers=headers
        )
        
        if not leads_response.ok:
            print(f"Error fetching leads: {leads_response.status_code}")
            leads = []
        else:
            leads = leads_response.json()

        # Fetch all agents for the agency
        agents_response = requests.get(
            f'{base_url}/api/agency/agents/{agency_data["id"]}/',
            headers=headers
        )
        
        if not agents_response.ok:
            print(f"Error fetching agents: {agents_response.status_code}")
            agents = []
        else:
            agents = agents_response.json()

        context = {
            'leads': leads,
            'agents': agents,
            'agency': agency_data
        }

        return render(request, 'agency_leads.html', context)

    except Exception as e:
        print(f"Error in agency leads view: {str(e)}")
        return redirect('/login')

@securedRoute
def agency_payments(request):
    base_url = request.build_absolute_uri('/')[:-1]
    access_token = request.session.get('access_token')
    agency_data = request.session.get('agencyData')

    if not agency_data:
        return redirect('login')

    headers = {'Authorization': f'Bearer {access_token}'}

    try:
        # Fetch all successful leads for the agency first
        leads_response = requests.get(
            f'{base_url}/api/leads/by-agency/{agency_data["id"]}/',
            headers=headers
        )
        
        if not leads_response.ok:
            print(f"Error fetching leads: {leads_response.status_code}")
            leads = []
        else:
            # Filter only successful leads (Commission Paid status)
            leads = leads_response.json()

        # For each successful lead, fetch its commission details
        payments_data = []
        for lead in leads:
            #print(f"Processing lead: {lead}")
            try:
                commission_response = requests.get(
                    f'{base_url}/api/commissions/by-lead/{lead["id"]}/',
                    headers=headers
                )
                
                if commission_response.ok:
                    commission = commission_response.json()
                    # Combine lead and commission data
                    print(f"Commission: {commission}")
                    payment_info = {
                        'id': commission['id'],
                        'lead_id': lead['id'],
                        'property': lead['property'],
                        'leadData': lead,
                        'spotter': lead['spotter'],
                        'property': lead['property'],
                        'spotter_id': lead['spotter']['id'],
                        'commissionAmount': lead['property']['commission'],
                        'assigned_agent': lead['assigned_agent'],
                        'created_at': commission['created_at'],
                        'paid_at': commission['paid_at'],
                        'amount': commission['amount'],
                        'status': commission['status'],
                        'payment_reference': commission.get('payment_reference'),
                        'notes': commission.get('notes')
                    }
                    payments_data.append(payment_info)
                else:
                    # payment_info empty
                    payment_info = {
                        'id': None,
                        'lead_id': lead['id'],
                        'property': lead['property'],
                        'spotter': lead['spotter'],
                        'property': lead['property'],
                        'leadData': lead,
                        'spotter_id': lead['spotter']['id'],
                        'commissionAmount': lead['property']['commission'],
                        #'commissionAmount': commission['amount'],
                        'assigned_agent': lead['assigned_agent'],
                        'created_at': None,
                        'paid_at': None,
                        'amount': 0,
                        'status': "Unpaid",
                        'payment_reference': None,
                        'notes': None
                    }
                    payments_data.append(payment_info)
                    print("Property comission amount: ", lead['property']['commission'])

            except Exception as e:
                print(f"Error processing commission for lead {lead['id']}: {str(e)}")
                continue

        context = {
            'agency': agency_data,
            'payments': payments_data
        }

        # Calculate some summary statistics for possible future use
        summary_stats = {
            'total_payments': len(payments_data),
            'pending_payments': sum(1 for p in payments_data if p['status'] == 'Pending'),
            'completed_payments': sum(1 for p in payments_data if p['status'] == 'Paid'),
            'total_amount': sum(float(p['amount']) for p in payments_data),
            'paid_amount': sum(float(p['amount']) for p in payments_data if p['status'] == 'Paid')
        }
        
        context['summary_stats'] = summary_stats

        return render(request, 'agency_spotter_payments.html', context)

    except Exception as e:
        print(f"Error in payments view: {str(e)}")
        return redirect('/login')



@securedRoute
def agency_properties(request):
    """
    View to display all properties assigned to an agency.
    Protected by securedRoute decorator.
    """
    base_url = request.build_absolute_uri('/')[:-1]
    access_token = request.session.get('access_token')
    agency_data = request.session.get('agencyData')

    if not agency_data:
        return redirect('login')

    headers = {'Authorization': f'Bearer {access_token}'}

    try:
        # Fetch all leads for the agency
        leads_response = requests.get(
            f'{base_url}/api/leads/by-agency/{agency_data["id"]}/',
            headers=headers
        )

        if not leads_response.ok:
            print(f"Error fetching leads: {leads_response.status_code}")
            properties_data = []
        else:
            properties_data = leads_response.json()

        # Calculate summary statistics
        summary_stats = {
            'total_properties': len(properties_data),
            'new_submissions': sum(1 for p in properties_data if p['property']['status'] == 'New Submission'),
            'assigned': sum(1 for p in properties_data if p['property']['status'] == 'Assigned'),
            'commission_paid': sum(1 for p in properties_data if p['property']['status'] == 'Commission Paid'),
            'total_value': sum(float(p['property']['price']) for p in properties_data if p['property']['price']),
        }

        context = {
            'agency': agency_data,
            'properties': properties_data,
            'summary_stats': summary_stats
        }

        # Pass the data to the template
        return render(request, 'agency_properties.html', context)

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return redirect('error_page')

@securedRoute
def agency_settings(request):
    """
    View to display and manage agency settings.
    Protected by securedRoute decorator.
    """
    base_url = request.build_absolute_uri('/')[:-1]
    access_token = request.session.get('access_token')
    agency_data = request.session.get('agencyData')

    if not agency_data:
        return redirect('login')

    headers = {'Authorization': f'Bearer {access_token}'}

    try:
        # Fetch detailed agency information
        agency_response = requests.get(
            f'{base_url}/api/agency/update/{agency_data["id"]}/',
            headers=headers
        )

        if not agency_response.ok:
            print(f"Error fetching agency details: {agency_response.status_code}")
            return redirect('error_page')

        agency_details = agency_response.json()

        # Fetch agency stats if needed
        # Example: total agents, total properties, etc.
        try:
            # Fetch all agents for the agency
            agents_response = requests.get(
                f'{base_url}/api/agents/by-agency/{agency_data["id"]}/',
                headers=headers
            )
            
            if agents_response.ok:
                agents = agents_response.json()
                total_agents = len(agents)
            else:
                total_agents = 0

            # Fetch agency's properties/leads count
            leads_response = requests.get(
                f'{base_url}/api/leads/by-agency/{agency_data["id"]}/',
                headers=headers
            )
            
            if leads_response.ok:
                leads = leads_response.json()
                total_properties = len(leads)
            else:
                total_properties = 0

            # Calculate additional stats
            agency_stats = {
                'total_agents': total_agents,
                'total_properties': total_properties,
                'active_agents': sum(1 for agent in agents if agent.get('is_active', False)) if agents_response.ok else 0,
                'pending_properties': sum(1 for lead in leads if lead['status'] == 'New Submission') if leads_response.ok else 0
            }

        except Exception as e:
            print(f"Error fetching agency stats: {str(e)}")
            agency_stats = {
                'total_agents': 0,
                'total_properties': 0,
                'active_agents': 0,
                'pending_properties': 0
            }

        context = {
            'agency': agency_details,
            'stats': agency_stats,
            'is_principal': request.user == agency_data.get('principal_user'),
            'AGENCYDATA': agency_data  # Required for base template
        }

        return render(request, 'agency_settings.html', context)

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return redirect('error_page')

@securedRoute
def agency_admin_profile(request):
    return render(request, 'agency_admin_profile.html')

#Agent Routes
@securedRoute
def agent_dashboard(request):
    context = {
        'page_title': 'Agent Dashboard'
    }
    return render(request, 'agents/dashboard.html', context)

@securedRoute
def agent_leads(request):
    context = {
        'page_title': 'Agent Leads'
    }
    return render(request, 'agents/leads.html', context)