from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AgencyViewSet

router = DefaultRouter()
router.register(r'agencies', AgencyViewSet, basename='agency')

urlpatterns = [
    path('', include(router.urls)),
]