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
from django.shortcuts import render, redirect

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

        print("Generating verification token...")
        try:
            # Generate the token string first
            verification_token = str(uuid.uuid4())
            print(f"Generated token: {verification_token}")
            
            # Create verification token record
            token = VerificationToken.objects.create(
                user=user,
                token=verification_token,
                expires_at=timezone.now() + timedelta(hours=24)
            )
            print(f"Token saved to database successfully")
        except Exception as token_error:
            print(f"Error creating token: {str(token_error)}")
            # Clean up: delete user if token creation fails
            user.delete()
            raise Exception(f"Failed to create verification token: {str(token_error)}")

        print("Preparing email verification...")
        try:
            # Prepare verification context
            verification_context = {
                'user': user,
                'verification_url': f"{settings.SITE_URL}/api/users/verify-email/{verification_token}/",
                'site_url': settings.SITE_URL
            }
            print(f"Email context prepared with URL: {verification_context['verification_url']}")
            
            # Render template content
            try:
                print("Rendering email template...")
                rendered_content = render_to_string(
                    'mail_templates/verification_email.html',
                    verification_context
                )
                print("Template rendered successfully")
            except Exception as template_error:
                print(f"Template rendering error: {str(template_error)}")
                raise Exception(f"Failed to render email template: {str(template_error)}")

            # Get or update email template
            print("Preparing email template...")
            email_template = EmailTemplate.objects.filter(name='verification_email').first()
            
            if email_template:
                print("Updating existing email template with new content")
                email_template.html_content = rendered_content
                email_template.save()
            else:
                print("Creating new email template")
                email_template = EmailTemplate.objects.create(
                    name='verification_email',
                    subject='Verify Your Email - Property Spotter',
                    html_content=rendered_content
                )

            print("Sending verification email...")
            email_template.send_email(
                to_email=user.email,
                context_data=verification_context
            )
            print("Verification email sent successfully")

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
        print("\n=== Starting Email Verification Process ===")
        print(f"Received verification request for token: {token}")
        
        # Debug: Print request information
        print("\nRequest Details:")
        print(f"Method: {request.method}")
        print(f"Path: {request.path}")
        print(f"Full URL: {request.build_absolute_uri()}")
        
        # Debug: Check all tokens in database
        print("\nDatabase Token Check:")
        all_tokens = VerificationToken.objects.all()
        print(f"Total tokens in database: {all_tokens.count()}")
        for t in all_tokens:
            print(f"Token: {t.token}, Used: {t.used}, User: {t.user.email}")
        
        # Debug: Try to find the specific token
        print(f"\nLooking for token: {token}")
        verification = VerificationToken.objects.filter(
            token=token,
            used=False
        ).first()
        
        print(f"Verification token found: {verification is not None}")
        
        if not verification:
            # Debug: Check why token wasn't found
            existing_token = VerificationToken.objects.filter(token=token).first()
            if existing_token:
                print("Token exists but might be used already")
                print(f"Token status - Used: {existing_token.used}")
                return Response({
                    'error': 'This verification link has already been used',
                    'redirect_url': f"{settings.SITE_URL}/login"
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                print("Token not found in database at all")
                return Response({
                    'error': 'Invalid verification token'
                }, status=status.HTTP_400_BAD_REQUEST)

        # Debug: User activation
        print("\nActivating user account:")
        user = verification.user
        print(f"User before activation - Email: {user.email}, Active: {user.is_active}")
        
        user.is_active = True
        user.save()
        
        print(f"User after activation - Email: {user.email}, Active: {user.is_active}")

        # Debug: Mark token as used
        print("\nUpdating token status:")
        verification.used = True
        verification.save()
        print("Token marked as used")

        # Send welcome email
        print("\nPreparing welcome email:")
        welcome_context = {
            'user': user,
            'dashboard_url': f"{settings.SITE_URL}/dashboard",
            'site_url': settings.SITE_URL
        }
        print("Welcome email context prepared")
       
        try:
            print("Attempting to send welcome email...")
            # Get or create welcome email template
            welcome_template, created = EmailTemplate.objects.get_or_create(
                name='welcome_email',
                defaults={
                    'subject': 'Welcome to Property Spotter',
                    'html_content': render_to_string(
                        'mail_templates/welcome_email.html',
                        welcome_context
                    )
                }
            )
            print(f"Welcome template {'created' if created else 'retrieved'}")
           
            # Send welcome email
            welcome_template.send_email(
                to_email=user.email,
                context_data=welcome_context
            )
            print("Welcome email sent successfully")
            
        except Exception as email_error:
            print(f"Warning: Welcome email could not be sent: {str(email_error)}")
            print(f"Detailed error: {email_error.__class__.__name__}")
            # Continue with verification even if welcome email fails
            pass

        print("\n=== Email Verification Process Completed Successfully ===")
        
        # Return response with redirect URL
        return redirect(f"{settings.SITE_URL}/login")
        return Response({
            'message': 'Email verified successfully',
            'redirect_url': f"{settings.SITE_URL}/login"
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print("\n=== Email Verification Process Failed ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("Full error details:", e)
        import traceback
        print("\nTraceback:")
        print(traceback.format_exc())
        
        return Response({
            'error': 'Verification failed. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@permission_classes([AllowAny])
def setup_agent_password(request, token):
    try:
        # Find the verification token
        verification = VerificationToken.objects.select_related('user').get(token=token)
        
        # Check if token has been used
        if verification.used:
            return render(request, 'setup_password.html', {
                'error': 'This link has already been used. Please contact support if you need assistance.'
            })
        
        # Store token in session for the API call
        request.session['setup_password_token'] = token
        
        return render(request, 'setup_password.html', {
            'token': token,
            'email': verification.user.email
        })
        
    except VerificationToken.DoesNotExist:
        return render(request, 'users/setup_password.html', {
            'error': 'Invalid or expired verification link. Please contact support.'
        })

@api_view(['POST'])
@permission_classes([])
def set_agent_password(request):
    print("Invoked!")
    try:
        token = request.data.get('token')
        password = request.data.get('password')
        
        if not token or not password:
            return Response({
                'error': 'Token and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            verification = VerificationToken.objects.select_related('user').get(token=token)
        except VerificationToken.DoesNotExist:
            return Response({
                'error': 'Invalid verification token'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if verification.used:
            return Response({
                'error': 'This verification token has already been used'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Validate password
        if len(password) < 8:
            return Response({
                'error': 'Password must be at least 8 characters long'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Set password and activate account
        user = verification.user
        user.set_password(password)
        user.is_active = True
        user.save()
        
        # Mark token as used
        verification.used = True
        verification.save()
        
        return Response({
            'message': 'Password set successfully. You can now login.'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_agent(request):
    from agency_management.models import Agency
    #Show all agent data
    print(request.data)
    all_data = request.data
    agency_registering = all_data['agency']['name']
    agency_registering_id = all_data['agency']['id']
    print("Agency registering:", agency_registering)
    try:
        # Check if the requesting user is an agency admin
        if request.user.role != 'Agency_Admin':
            return Response(
                {'error': 'Only agency administrators can register agents'},
                status=status.HTTP_403_FORBIDDEN
            )

        data = request.data
        print("Received agent registration data:", data)

        # Basic validation
        required_fields = ['email', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                print(f"Validation failed: {field} is missing")
                return Response(
                    {'error': f'{field} is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Generate username from email (take part before @)
        username = data['email'].split('@')[0]
        # If username exists, append numbers until unique
        base_username = username
        counter = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        # Check if email already exists
        if CustomUser.objects.filter(email=data['email']).exists():
            print(f"Email {data['email']} already exists")
            return Response(
                {'error': 'Email already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )

        print("Creating agent instance...")
        try:
            agency_obj = Agency.objects.get(id=agency_registering_id)
            # Create user instance with is_active=False until they set their password
            agent = CustomUser(
                username=username,
                email=data['email'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                role='Agent',
                is_active=False,  # Will be set to True when they set their password
                profile_complete=False,
                agency=agency_obj  # Set the agency to the admin's agency
            )
            
            if 'phone' in data:
                agent.phone = data['phone']
            
            agent.save()
            print(f"Agent created successfully with ID: {agent.id}")
        except Exception as user_error:
            print(f"Error creating agent: {str(user_error)}")
            raise Exception(f"Failed to create agent: {str(user_error)}")

        print("Generating verification token...")
        try:
            # Generate the token
            verification_token = str(uuid.uuid4())
            print(f"Generated token: {verification_token}")
            
            # Create verification token record
            token = VerificationToken.objects.create(
                user=agent,
                token=verification_token,
                expires_at=timezone.now() + timedelta(hours=48)  # 48 hours to set up password
            )
            print(f"Token saved to database successfully")
        except Exception as token_error:
            print(f"Error creating token: {str(token_error)}")
            agent.delete()
            raise Exception(f"Failed to create verification token: {str(token_error)}")

        print("Preparing welcome email...")
        try:
            # Prepare welcome email context
            setup_password_url = f"{settings.SITE_URL}/users/setup-password/{verification_token}/"
            welcome_context = {
                'user': agent,
                'agency_name': agency_registering,
                'setup_password_url': setup_password_url,
                'site_url': settings.SITE_URL
            }
            print(f"Email context prepared with URL: {setup_password_url}")
            
            try:
                print("Rendering email template...")
                rendered_content = render_to_string(
                    'mail_templates/agent_confirmation.html',
                    welcome_context
                )
                print("Template rendered successfully")
            except Exception as template_error:
                print(f"Template rendering error: {str(template_error)}")
                raise Exception(f"Failed to render email template: {str(template_error)}")

            # Get or update email template
            print("Preparing email template...")
            email_template = EmailTemplate.objects.filter(name='agent_confirmation.html').first()
            
            if email_template:
                print("Updating existing email template with new content")
                email_template.html_content = rendered_content
                email_template.save()
            else:
                print("Creating new email template")
                email_template = EmailTemplate.objects.create(
                    name='agent_welcome_email',
                    subject=f'Welcome to {agency_registering} on {settings.SITE_NAME} - Set Up Your Agent Account',
                    html_content=rendered_content
                )

            print("Sending welcome email...")
            email_template.send_email(
                to_email=agent.email,
                context_data=welcome_context
            )
            print("Welcome email sent successfully")

        except Exception as email_error:
            print(f"Error in email process: {str(email_error)}")
            token.delete()
            agent.delete()
            raise Exception(f"Failed to send welcome email: {str(email_error)}")

        print("Agent registration process completed successfully")
        return Response({
            'message': 'Agent registered successfully. A welcome email has been sent with setup instructions.',
            'user_id': agent.id
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        print(f"Final error catch: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)