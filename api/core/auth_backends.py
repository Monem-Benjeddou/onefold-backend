"""
Custom authentication backends to handle User model transitions.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ValidationError


class TransitionalAuthBackend(ModelBackend):
    """
    Authentication backend that handles the transition from UUID to integer primary keys.
    This backend gracefully handles session data that contains UUID values.
    """
    
    def get_user(self, user_id):
        """
        Get user by ID, handling both UUID and integer formats during transition.
        """
        User = get_user_model()
        
        try:
            # First try to get user by integer ID (new format)
            return User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValidationError, ValueError):
            # If that fails, try to get user by UUID (old format)
            # This handles existing session data with UUID values
            try:
                return User.objects.get(pk=str(user_id))
            except (User.DoesNotExist, ValidationError, ValueError):
                return None
