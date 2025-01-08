from django.urls import path
from . import views


urlpatterns = [
	    path('', views.index, name='index'),  # Render index page
	    path('login/', views.login_view, name='loginview'),
	    path('register/', views.spotter_register, name='register'),
	    path('dashboard/', views.dashboard, name='dashboard'),
	    path('leads/', views.myLeads, name='leads'),
	    path('history/', views.myHistory, name='history'),
	    path('profile/', views.myProfile, name='profile'),
	    path('newLead/', views.newLead, name='newLead'),
	    path('sessionSave/', views.sessionSave, name='sessionSave'),
	    path('logout/', views.logout, name='logout'),
	    path('token/', views.token, name='token'),

	    # Agency routes
	    path('agency/', views.agency_dashboard, name='agency'),
]