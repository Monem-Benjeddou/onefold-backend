"""
Custom CSRF middleware that exempts API endpoints from CSRF protection.
"""

from django.middleware.csrf import CsrfViewMiddleware


class CsrfExemptApiMiddleware(CsrfViewMiddleware):
    """
    CSRF middleware that exempts API endpoints from CSRF protection.
    """
    
    def process_view(self, request, callback, callback_args, callback_kwargs):
        # Require CSRF protection for authentication endpoints ONLY when using session auth.
        # This keeps browser session flows protected, while allowing token-based and Swagger calls to work.
        auth_protected_paths = [
            '/api/v1/auth/register/',
            '/api/v1/auth/login/',
            '/api/v1/auth/logout/',
            '/api/v1/auth/forgot-password/',
            '/api/v1/auth/reset-password/',
            '/api/v1/auth/change-password/',
        ]

        if request.path in auth_protected_paths:
            has_session_cookie = 'sessionid' in request.COOKIES or (
                'HTTP_COOKIE' in request.META and 'sessionid=' in request.META.get('HTTP_COOKIE', '')
            )
            if has_session_cookie:
                # Enforce CSRF when a Django session is present
                return super().process_view(request, callback, callback_args, callback_kwargs)
            # No session cookie → treat as token-based API call; skip CSRF
            return None
        
        # Exempt other API endpoints from CSRF protection
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
