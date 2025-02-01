from django.urls import path
from . import views

urlpatterns = [
   path('', views.lead_list),
   path('by-spotter/<uuid:spotter_id>/', views.leads_by_spotter),
   path('by-agency/<uuid:agency_id>/', views.leads_by_agency),
   path('<uuid:lead_id>/assign-agency/', views.assign_to_agency),
   path('<uuid:lead_id>/assign-agent/', views.assign_to_agent),
   path('new/', views.create_lead),
   path('<uuid:lead_id>/mark-paid/', views.mark_lead_commission_paid, name='mark-lead-paid'),

   path('by-agent/<str:agent_id>/', views.agent_leads, name='agent-leads'),
   path('agent-stats/<str:agent_id>/', views.agent_lead_stats, name='agent-lead-stats'),
   path('<str:lead_id>/set-commission/', views.set_lead_commission, name='set-lead-commission'),
   path('<str:lead_id>/update-status/', views.update_lead_status, name='update-lead-status'),
]