from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_users, name='list-users'),  # GET all users
    path('<uuid:pk>/', views.get_user, name='get-user'),  # GET single user
    path('create/', views.create_user, name='create-user'),  # POST new user
    path('<uuid:pk>/update/', views.update_user, name='update-user'),  # PATCH update user
    path('<uuid:pk>/delete/', views.delete_user, name='delete-user'),  # DELETE user

    # Authentication routes
    path('login/', views.login_user, name='login-user'),  # POST to log in and get JWT
    path('refresh/', views.login_user, name='token-refresh'),  # Refresh expired token
    path('logout/', views.logout_user, name='logout-user'),  # Logout user (optional)
]