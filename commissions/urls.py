from django.urls import path
from . import views

urlpatterns = [
   path('', views.get_all_commissions),
   path('by-lead/<uuid:lead_id>/', views.get_commission_by_lead),
   path('by-spotter/<uuid:spotter_id>/', views.get_commissions_by_spotter),
]