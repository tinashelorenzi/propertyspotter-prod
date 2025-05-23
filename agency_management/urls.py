from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AgencyViewSet
from . import views
from .views import AgencyUpdateView

router = DefaultRouter()
router.register(r'agencies', AgencyViewSet, basename='agency')

urlpatterns = [
    path('', views.get_all_agencies, name='agency-list'),
    path('get-agency-by-admin/<uuid:admin_id>/', views.get_agency_by_admin, name='get-agency-by-admin'),
    path('agents/<str:agency_id>/', views.get_agency_agents, name='agency-agents'),
    path('update/<uuid:agency_id>/', AgencyUpdateView.as_view(), name='agency-update'),
]