"""
Middleware to fix session data during UUID to integer transition.
"""

from django.contrib.auth import SESSION_KEY


class SessionTransitionMiddleware:
    """
    Middleware that clears session data with UUID values during the transition
    from UUID to integer primary keys.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if session contains UUID data
        if hasattr(request, 'session') and request.session:
            session_key = request.session.get(SESSION_KEY)
            if session_key:
                # Check if the session key is a UUID (old format)
                try:
                    # Try to convert to int - if it fails, it's likely a UUID
                    int(session_key)
                except (ValueError, TypeError):
                    # This is a UUID, clear the session
                    request.session.flush()
        
        response = self.get_response(request)
        return response
