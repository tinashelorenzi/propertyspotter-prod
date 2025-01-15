from django.urls import path
from . import views
from .views import CommissionCreateView

urlpatterns = [
   path('', views.get_all_commissions),
   path('by-lead/<uuid:lead_id>/', views.get_commission_by_lead),
   path('by-spotter/<uuid:spotter_id>/', views.get_commissions_by_spotter),
   path('<uuid:commission_id>/mark-paid/', views.mark_commission_paid, name='mark-commission-paid'),

   path('process-payment/', views.process_payment, name='process-payment'),
   path('create/', CommissionCreateView.as_view(), name='commission-create'),
]