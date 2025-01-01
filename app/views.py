from django.shortcuts import render

# Create your views here.

def index(request):
	return render(request, 'index.html')

def login_view(request):
    return render(request, 'login.html')

def dashboard(request):
	return render(request, 'spotter_dashboard.html')