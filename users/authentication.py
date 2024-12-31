from rest_framework import authentication
from rest_framework import exceptions
from django.contrib.auth import get_user_model
import jwt
from django.conf import settings

User = get_user_model()

class BodyTokenAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        # Get token from request body
        token = None
        if request.method == 'POST':  # Only check body for POST requests
            token = request.data.get('token')
        
        if not token:
            return None

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user = User.objects.get(id=payload['user_id'])
            return (user, None)
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Access token has expired')
        except (jwt.DecodeError, User.DoesNotExist):
            raise exceptions.AuthenticationFailed('Invalid token')