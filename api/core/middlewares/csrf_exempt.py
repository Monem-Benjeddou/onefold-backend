"""
Custom CSRF middleware that exempts API endpoints from CSRF protection.
"""

from django.middleware.csrf import CsrfViewMiddleware


class CsrfExemptApiMiddleware(CsrfViewMiddleware):
    """
    CSRF middleware that exempts API endpoints from CSRF protection.
    """
    
    def process_view(self, request, callback, callback_args, callback_kwargs):
        # Exempt API endpoints from CSRF protection
        if request.path.startswith('/api/'):
            return None
        
        # Also exempt specific auth endpoints that might not start with /api/
        auth_exempt_paths = [
            '/account/auth/login/',
            '/account/auth/register/',
            '/account/auth/logout/',
            '/account/auth/me/',
            '/account/auth/password/reset/',
            '/account/auth/password/reset/confirm/',
            '/account/auth/verify-email/',
            '/account/auth/jwt/token/',
            '/account/auth/jwt/refresh/',
            '/account/auth/jwt/verify/',
        ]
        
        if request.path in auth_exempt_paths:
            return None
        
        # For non-API endpoints, use the default CSRF behavior
        return super().process_view(request, callback, callback_args, callback_kwargs)
