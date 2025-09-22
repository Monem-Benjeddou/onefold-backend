"""
Monkey patch Django's authentication to handle UUID to integer transition.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth import SESSION_KEY
from django.core.exceptions import ValidationError


def patched_get_user(request):
    """
    Patched version of Django's get_user function that handles UUID to integer transition.
    """
    from django.contrib.auth import _get_user_session_key
    
    try:
        # Try to get the user ID from session using Django's original method
        user_id = _get_user_session_key(request)
        if not user_id:
            return None
        
        User = get_user_model()
        return User.objects.get(pk=user_id)
        
    except (ValidationError, ValueError):
        # If conversion fails (UUID to int), clear the session and return None
        if hasattr(request, 'session'):
            request.session.flush()
        return None
    except User.DoesNotExist:
        return None


def apply_auth_patch():
    """
    Apply the authentication patch to handle UUID to integer transition.
    """
    from django.contrib import auth
    
    # Monkey patch the get_user function
    auth.get_user = patched_get_user
