"""
JWT Authentication Middleware for Django Channels

Production-ready middleware with comprehensive error handling, logging,
security features, and proper token validation.
"""

import jwt
import logging
from urllib.parse import parse_qs
from typing import Optional, Dict, Any

from asgiref.sync import sync_to_async
from channels.auth import AuthMiddlewareStack
from channels.middleware import BaseMiddleware
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from core.utilities.cache_utils import cache_manager
from django.utils import timezone
from datetime import datetime, timedelta

User = get_user_model()
logger = logging.getLogger(__name__)


@sync_to_async
def get_user_by_id(user_id: str) -> Optional[User]:
    """
    Retrieve user by UUID with caching for performance.
    """
    cache_key = f"websocket_user_{user_id}"

    cached_user = cache_manager.get(cache_key)
    if cached_user:
        return cached_user

    try:

        from uuid import UUID

        uuid_obj = UUID(str(user_id))

        user = User.objects.select_related().get(id=uuid_obj)

        cache_manager.set(cache_key, user, 300)
        return user
    except (User.DoesNotExist, ValueError) as e:
        logger.warning(f"User with ID {user_id} not found or invalid UUID: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving user {user_id}: {str(e)}")
        return None


class JWTAuthMiddleware(BaseMiddleware):
    """
    JWT Authentication Middleware for WebSocket connections.

    Supports multiple token sources: query parameters, headers, and cookies.
    Includes comprehensive security features and error handling.
    """

    def __init__(self, inner):
        super().__init__(inner)
        self.token_expiry_buffer = getattr(settings, "JWT_EXPIRY_BUFFER_SECONDS", 60)

    async def __call__(self, scope, receive, send):
        """
        Main middleware entry point with comprehensive token validation.
        """

        scope["user"] = AnonymousUser()
        scope["jwt_payload"] = None
        scope["auth_method"] = None

        try:

            token = await self.extract_token(scope)

            if not token:
                logger.debug("No JWT token provided in WebSocket connection")
                return await super().__call__(scope, receive, send)

            payload = await self.validate_token(token)

            if not payload:
                logger.warning("Invalid JWT token in WebSocket connection")
                return await super().__call__(scope, receive, send)

            user = await self.get_user_from_payload(payload)

            if user:
                scope["user"] = user
                scope["jwt_payload"] = payload
                scope["auth_method"] = "jwt"
                logger.info(
                    f"WebSocket authenticated user: {user.username} (ID: {user.id})"
                )
            else:
                logger.warning(
                    f"User not found for JWT payload: {payload.get('user_id')}"
                )

        except Exception as e:
            logger.error(
                f"Error in JWT authentication middleware: {str(e)}", exc_info=True
            )

        return await super().__call__(scope, receive, send)

    async def extract_token(self, scope) -> Optional[str]:
        """
        Extract JWT token from query parameters, headers, or cookies.

        Priority: query_string > Authorization header > cookie
        """

        query_string = parse_qs(scope.get("query_string", b"").decode())
        token = query_string.get("token", [None])[0]
        if token:
            return token.strip()

        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization")
        if auth_header:
            auth_value = auth_header.decode().strip()
            if auth_value.startswith("Bearer "):
                return auth_value[7:].strip()

        cookie_header = headers.get(b"cookie")
        if cookie_header:
            cookies = self.parse_cookies(cookie_header.decode())
            return cookies.get("jwt_token")

        return None

    def parse_cookies(self, cookie_header: str) -> Dict[str, str]:
        """Parse cookie header into dictionary."""
        cookies = {}
        for cookie in cookie_header.split(";"):
            if "=" in cookie:
                key, value = cookie.strip().split("=", 1)
                cookies[key] = value
        return cookies

    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate JWT token with comprehensive security checks.
        """
        try:

            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "require": ["exp", "iat", "user_id"],
                },
            )

            if not await self.validate_payload_security(payload):
                return None

            return payload

        except jwt.ExpiredSignatureError:
            logger.debug("JWT token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.debug(f"Invalid JWT token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error validating JWT: {str(e)}")
            return None

    async def validate_payload_security(self, payload: Dict[str, Any]) -> bool:
        """
        Additional security validation for JWT payload.
        """

        required_fields = ["user_id", "exp", "iat"]
        if not all(field in payload for field in required_fields):
            logger.warning("JWT payload missing required fields")
            return False

        user_id = payload.get("user_id")
        if not user_id:
            logger.warning("Missing user_id in JWT payload")
            return False

        try:
            from uuid import UUID

            UUID(str(user_id))
        except (ValueError, TypeError):
            logger.warning(f"Invalid user_id format in JWT payload: {user_id}")
            return False

        issued_at = payload.get("iat")
        if issued_at:
            max_age = getattr(settings, "JWT_MAX_AGE_DAYS", 30)
            if datetime.now().timestamp() - issued_at > (max_age * 24 * 3600):
                logger.warning("JWT token is too old")
                return False

        if await self.is_token_blacklisted(payload):
            logger.warning("JWT token is blacklisted")
            return False

        return True

    async def is_token_blacklisted(self, payload: Dict[str, Any]) -> bool:
        """
        Check if token is blacklisted (optional security feature).
        """

        return False

    async def get_user_from_payload(self, payload: Dict[str, Any]) -> Optional[User]:
        """
        Get user from JWT payload with UUID validation.
        """
        try:
            user_id = str(payload["user_id"])
            return await get_user_by_id(user_id)
        except (KeyError, TypeError) as e:
            logger.error(f"Error extracting user_id from payload: {str(e)}")
            return None


def JWTAuthMiddlewareStack(inner):
    """
    Create JWT authentication middleware stack.

    This combines JWT authentication with Django's built-in auth middleware
    for maximum compatibility and security.
    """
    return JWTAuthMiddleware(AuthMiddlewareStack(inner))
