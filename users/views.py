from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .models import CustomUser, Agency, VerificationToken
from .authentication import BodyTokenAuthentication
from .serializers import UserSerializer
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.hashers import make_password
from mailer.models import EmailTemplate
from django.utils.crypto import get_random_string
from django.template.loader import render_to_string
import jwt
from django.conf import settings
import uuid
#Render
from django.shortcuts import render

User = get_user_model()


def login_view(request):
    return render(request, 'login.html')

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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user(request, pk):
    # Fetch the user with the provided primary key (UUID)
    user_requested = get_object_or_404(CustomUser, pk=pk)

    # Serialize the user data
    serializer = UserSerializer(user_requested)

    # Return the serialized data
    return Response(serializer.data, status=status.HTTP_200_OK)

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

# views.py
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    try:
        user = request.user
        form_data = request.data

        # Password validation
        if form_data.get('new_password'):
            if not user.check_password(form_data.get('old_password', '')):
                return Response({
                    'status': 'error',
                    'message': 'Current password is incorrect'
                }, status=400)
            
            if form_data.get('new_password') != form_data.get('confirm_password'):
                return Response({
                    'status': 'error',
                    'message': 'New passwords do not match'
                }, status=400)
            # Update password
            user.set_password(form_data['new_password'])

        # Update basic info
        allowed_fields = [
            'first_name', 'last_name', 'phone',
            'bank_name', 'bank_branch_code', 'account_number',
            'account_name', 'account_type'
        ]

        # Split validation by field type
        # Basic info validation
        if user.role == 'Spotter' and any(
            not form_data.get(f) for f in [
                'bank_name', 'bank_branch_code', 'account_number',
                'account_name', 'account_type'
            ]
        ):
            return Response({
                'status': 'error',
                'message': 'All banking fields are required for Spotters'
            }, status=400)

        # Update all allowed fields
        for field in allowed_fields:
            if field in form_data:
                setattr(user, field, form_data[field])

        # Handle profile image
        if 'profile_image' in request.FILES:
            user.profile_image = request.FILES['profile_image']
            
        # Mark profile as complete if all required fields are filled
        if user.role == 'Spotter':
            user.profile_complete = all([
                user.first_name, user.last_name, user.phone,
                user.bank_name, user.bank_branch_code,
                user.account_number, user.account_name, user.account_type
            ])

        user.save()
        
        return Response({
            'status': 'success',
            'message': 'Profile updated successfully'
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=400)



@api_view(['DELETE'])
def delete_user(request, pk):
    # Extract the token from the request body
    token = request.data.get('token', None)

    # Check if the token is provided
    if not token:
        return Response(
            {"error": "Authentication token is required."},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Authenticate the token
    jwt_auth = JWTAuthentication()
    try:
        validated_token = jwt_auth.get_validated_token(token)
        user = jwt_auth.get_user(validated_token)
    except Exception:
        return Response(
            {"error": "Invalid or expired token."},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Fetch the user to be deleted
    user_to_delete = get_object_or_404(CustomUser, pk=pk)

    # Check if the authenticated user has permission to delete (optional)
    if not user.is_staff and user.id != user_to_delete.id:
        return Response(
            {"error": "You do not have permission to delete this user."},
            status=status.HTTP_403_FORBIDDEN
        )

    # Delete the user
    user_to_delete.delete()
    return Response(
        {"message": "User successfully deleted."},
        status=status.HTTP_204_NO_CONTENT
    )

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    try:
        data = request.data
        print("Received registration data:", data)

        # Basic validation
        required_fields = ['username', 'email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                print(f"Validation failed: {field} is missing")
                return Response(
                    {'error': f'{field} is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Check if username or email already exists
        if CustomUser.objects.filter(username=data['username']).exists():
            print(f"Username {data['username']} already exists")
            return Response(
                {'error': 'Username already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if CustomUser.objects.filter(email=data['email']).exists():
            print(f"Email {data['email']} already exists")
            return Response(
                {'error': 'Email already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )

        print("Creating user instance...")
        try:
            # Create user instance
            user = CustomUser(
                username=data['username'],
                email=data['email'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                role='Spotter',
                is_active=False,
                profile_complete=False
            )
            
            user.password = make_password(data['password'])
            
            if 'profile_image' in request.FILES:
                print("Processing profile image...")
                user.profile_image = request.FILES['profile_image']
            
            if 'phone' in data:
                user.phone = data['phone']
            
            user.save()
            print(f"User created successfully with ID: {user.id}")
        except Exception as user_error:
            print(f"Error creating user: {str(user_error)}")
            raise Exception(f"Failed to create user: {str(user_error)}")

        print("Creating verification token...")
        try:
            # Create verification token
            token = VerificationToken.objects.create(
                user=user,
                token=str(uuid.uuid4()),
                expires_at=timezone.now() + timedelta(hours=24)
            )
            print(f"Token created: {token.token}")
        except Exception as token_error:
            print(f"Error creating token: {str(token_error)}")
            # Clean up: delete user if token creation fails
            user.delete()
            raise Exception(f"Failed to create verification token: {str(token_error)}")

        print("Preparing email context...")
        try:
            verification_context = {
                'user': user,
                'verification_url': f"{settings.SITE_URL}/verify-email/{token.token}",
                'site_url': settings.SITE_URL
            }
            print("Email context:", verification_context)
            
            # First try to render the template separately
            print("Attempting to render template...")
            try:
                rendered_content = render_to_string(
                    'mail_templates/verification_email.html',
                    verification_context
                )
                print("Template rendered successfully")
            except Exception as template_error:
                print(f"Template rendering error: {str(template_error)}")
                raise Exception(f"Failed to render email template: {str(template_error)}")

            print("Getting or creating EmailTemplate...")
            email_template, created = EmailTemplate.objects.get_or_create(
                name='verification_email',
                defaults={
                    'subject': 'Verify Your Email - Property Spotter',
                    'html_content': rendered_content
                }
            )
            """
            print("Creating EmailTemplate...")
            email_template = EmailTemplate.objects.create(
                name='verification_email',
                subject='Verify Your Email - Property Spotter',
                html_content=rendered_content
            )
            """
            print("EmailTemplate created successfully")

            print("Sending email...")
            email_template.send_email(
                to_email=user.email,
                context_data=verification_context
            )
            print("Email sent successfully")

        except Exception as email_error:
            print(f"Error in email process: {str(email_error)}")
            # Clean up: delete user and token if email fails
            token.delete()
            user.delete()
            raise Exception(f"Failed to send verification email: {str(email_error)}")

        print("Registration process completed successfully")
        return Response({
            'message': 'Registration successful. Please check your email for verification.',
            'user_id': user.id
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        print(f"Final error catch: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def verify_email(request, token):
    try:
        # Get token object
        verification = VerificationToken.objects.filter(
            token=token,
            used=False,
            expires_at__gt=timezone.now()
        ).first()

        if not verification:
            return Response({
                'error': 'Invalid or expired verification token'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Activate user
        user = verification.user
        user.is_active = True
        user.save()

        # Mark token as used
        verification.used = True
        verification.save()

        # Send welcome email
        welcome_context = {
            'user': user,
            'dashboard_url': f"{settings.SITE_URL}/dashboard",
            'site_url': settings.SITE_URL
        }
        
        EmailTemplate.objects.create(
            name='welcome_email',
            subject='Welcome to Property Spotter',
            html_content=render_to_string(
                'mail_templates/welcome_email.html',
                welcome_context
            )
        ).send_email(to_email=user.email, context_data=welcome_context)

        return Response({
            'message': 'Email verified successfully. You can now log in.'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)