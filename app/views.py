from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from .decorators import securedRoute
import json

CustomUser = get_user_model()
# Create your views here.

def index(request):
	return render(request, 'index.html')

def login_view(request):
    return render(request, 'login.html')

@securedRoute
def dashboard(request):
	return render(request, 'spotter_dashboard.html')

@securedRoute
def myLeads(request):
    return render(request, 'spotter_leads.html')

@securedRoute
def myHistory(request):
    return render(request, 'spotter_history.html')

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
    return JsonResponse({'token': request.session.get('access_token')})

def logout(request):
    request.session.flush()
    return redirect('/')