# leads/urls.py
from django.urls import path
from . import views

app_name = 'leads'

urlpatterns = [
    # Base lead management
    path('', views.list_leads, name='list-leads'),                        # POST: List all leads with filtering
    path('get/', views.get_lead, name='get-lead'),                       # POST: Get single lead details
    path('create/', views.create_lead, name='create-lead'),              # POST: Create new lead
    path('update/', views.update_lead, name='update-lead'),              # POST: Update lead details
    path('delete/', views.delete_lead, name='delete-lead'),              # POST: Delete a lead
    
    # Agency assignment endpoints
    path('push-to-agency/', views.push_lead_to_agency, name='push-to-agency'),    # POST: Push lead to agency
    path('assign-to-agent/', views.assign_lead_to_agent, name='assign-to-agent'), # POST: Assign lead to agent
]