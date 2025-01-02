from django.urls import path
from . import views


urlpatterns = [
	    path('', views.index, name='index'),  # Render index page
	    path('login/', views.login_view, name='loginview'),
	    path('dashboard/', views.dashboard, name='dashboard'),
	    path('leads/', views.myLeads, name='leads'),
	    path('history/', views.myHistory, name='history'),
	    path('sessionSave/', views.sessionSave, name='sessionSave'),
	    path('logout/', views.logout, name='logout'),
]