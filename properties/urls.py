# properties/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_properties, name='list-properties'),
    path('get/', views.get_property, name='get-property'),
    path('create/', views.create_property, name='create-property'),
    path('update/', views.update_property, name='update-property'),
    path('delete/', views.delete_property, name='delete-property'),
]