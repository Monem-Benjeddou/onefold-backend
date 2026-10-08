from drf_spectacular.contrib.rest_framework_simplejwt import SimpleJWTScheme


class SessionJWTScheme(SimpleJWTScheme):
    """Document SessionJWTAuthentication as the usual bearer JWT."""

    target_class = "apps.accounts.authentication.SessionJWTAuthentication"
    name = "jwtAuth"
