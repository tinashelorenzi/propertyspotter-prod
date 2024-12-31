from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .models import CustomUser, Agency
from .authentication import BodyTokenAuthentication
from .serializers import UserSerializer
import jwt
from django.conf import settings

User = get_user_model()

def verify_token(token):
    """Verify JWT token and return user"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user = User.objects.get(id=payload['user_id'])
        return user
    except (jwt.DecodeError, User.DoesNotExist):
        return None

@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """Login with email and password"""
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response(
            {"error": "Both email and password are required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email=email)
        if not user.check_password(password):
            return Response(
                {"error": "Invalid credentials"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        refresh = RefreshToken.for_user(user)
        from django.utils import timezone
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        return Response({
            'token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': UserSerializer(user).data
        })
    except User.DoesNotExist:
        return Response(
            {"error": "Invalid credentials"}, 
            status=status.HTTP_401_UNAUTHORIZED
        )

@api_view(['POST'])
@authentication_classes([BodyTokenAuthentication])
@permission_classes([IsAuthenticated])
def list_users(request):
    """List all users - only accessible by Admin"""
    user = request.user  # Now we can directly access the authenticated user
    
    if user.role != 'Admin':
        return Response(
            {"error": "Only Admin users can list all users"}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    users = CustomUser.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def get_user(request):
    """Get user details - Admin can get any user, Agency_Admin can only get users from their agency"""
    token = request.data.get('token')
    email = request.data.get('email')
    
    requesting_user = verify_token(token)
    if not requesting_user:
        return Response(
            {"error": "Invalid token"}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        requested_user = User.objects.get(email=email)
        
        # Check permissions
        if requesting_user.role == 'Admin':
            pass  # Admin can access any user
        elif requesting_user.role == 'Agency_Admin':
            if requested_user.agency != requesting_user.agency:
                return Response(
                    {"error": "You can only access users from your agency"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            return Response(
                {"error": "Insufficient permissions"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        serializer = UserSerializer(requested_user)
        return Response(serializer.data)
        
    except User.DoesNotExist:
        return Response(
            {"error": "User not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
def refresh_token(request):
    """Refresh access token using refresh token"""
    refresh_token = request.data.get('refresh_token')
    
    if not refresh_token:
        return Response(
            {"error": "Refresh token is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        refresh = RefreshToken(refresh_token)
        user = User.objects.get(id=refresh.payload.get('user_id'))
        
        return Response({
            'token': str(refresh.access_token),
            'user': UserSerializer(user).data
        })
    except Exception as e:
        return Response(
            {"error": "Invalid refresh token"}, 
            status=status.HTTP_401_UNAUTHORIZED
        )

@api_view(['POST'])
def logout_user(request):
    """Logout user by blacklisting their refresh token"""
    refresh_token = request.data.get('refresh_token')
    
    if not refresh_token:
        return Response(
            {"error": "Refresh token is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()  # This will blacklist the refresh token
        return Response(
            {"message": "Successfully logged out"}, 
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": "Invalid refresh token"}, 
            status=status.HTTP_401_UNAUTHORIZED
        )

@api_view(['POST'])
def create_user(request):
    """Create new user"""
    token = request.data.get('token')
    
    creating_user = verify_token(token)
    if not creating_user:
        return Response(
            {"error": "Invalid token"}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Remove token from data before serialization
    user_data = request.data.copy()
    user_data.pop('token')
    
    # Handle agency assignment based on role
    if creating_user.role != 'Admin':
        if creating_user.role != 'Agency_Admin':
            return Response(
                {"error": "Only Admin or Agency_Admin can create users"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        # Force agency assignment to creator's agency for Agency_Admin
        user_data['agency_assigned'] = creating_user.agency.id
    
    serializer = UserSerializer(data=user_data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            UserSerializer(user).data, 
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def update_user(request):
    """Update user details"""
    token = request.data.get('token')
    email = request.data.get('email')
    
    updating_user = verify_token(token)
    if not updating_user:
        return Response(
            {"error": "Invalid token"}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        user_to_update = User.objects.get(email=email)
        
        # Check permissions
        if updating_user.role == 'Admin':
            pass  # Admin can update any user
        elif updating_user.role == 'Agency_Admin':
            if user_to_update.agency != updating_user.agency:
                return Response(
                    {"error": "You can only update users from your agency"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            return Response(
                {"error": "Insufficient permissions"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Remove token and email from data before serialization
        update_data = request.data.copy()
        update_data.pop('token')
        update_data.pop('email')
        
        serializer = UserSerializer(user_to_update, data=update_data, partial=True)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except User.DoesNotExist:
        return Response(
            {"error": "User not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
def delete_user(request):
    """Delete user"""
    token = request.data.get('token')
    email = request.data.get('email')
    
    deleting_user = verify_token(token)
    if not deleting_user:
        return Response(
            {"error": "Invalid token"}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        user_to_delete = User.objects.get(email=email)
        
        # Check permissions
        if deleting_user.role == 'Admin':
            pass  # Admin can delete any user
        elif deleting_user.role == 'Agency_Admin':
            if user_to_delete.agency != deleting_user.agency:
                return Response(
                    {"error": "You can only delete users from your agency"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            return Response(
                {"error": "Insufficient permissions"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        user_to_delete.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
        
    except User.DoesNotExist:
        return Response(
            {"error": "User not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )