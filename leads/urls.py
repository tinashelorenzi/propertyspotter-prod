from django.urls import path
from . import views

urlpatterns = [
   path('', views.lead_list),
   path('by-spotter/<uuid:spotter_id>/', views.leads_by_spotter),
   path('by-agency/<uuid:agency_id>/', views.leads_by_agency),
   path('<uuid:lead_id>/assign-agency/', views.assign_to_agency),
   path('<uuid:lead_id>/assign-agent/', views.assign_to_agent),
   path('create/', views.create_lead),
]