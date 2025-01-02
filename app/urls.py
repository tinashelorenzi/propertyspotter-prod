from django.urls import path
from . import views


urlpatterns = [
	    path('', views.index, name='index'),  # Render index page
	    path('login/', views.login_view, name='loginview'),
	    path('dashboard/', views.dashboard, name='dashboard'),
	    path('sessionSave/', views.sessionSave, name='sessionSave'),
]