from django.shortcuts import redirect
from functools import wraps

def securedRoute(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check if the session contains the 'loggedIn' key and it is True
        if not request.session.get('loggedIn', False):
            # If not logged in, redirect to the login page
            return redirect('login')  # Change 'login' to the actual URL name for your login view

        # If logged in, proceed with the view
        return view_func(request, *args, **kwargs)

    return _wrapped_view