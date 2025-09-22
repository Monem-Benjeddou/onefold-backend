"""
Cache control decorators and utilities that respect the ENABLE_CACHE setting.

This module provides decorators and utilities for controlling caching behavior
across the application. When ENABLE_CACHE is False, all cache operations are
bypassed and functions execute normally without any cache interactions.
"""

from functools import wraps
from typing import Any, Callable, Optional, Union
import logging
from django.core.cache import cache
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from rest_framework.response import Response

logger = logging.getLogger(__name__)


def is_cache_enabled() -> bool:
    """
    Check if caching is enabled globally.

    Returns:
        bool: True if caching is enabled, False otherwise
    """
    enable_cache = getattr(settings, "ENABLE_CACHE", True)
    if isinstance(enable_cache, str):
        return enable_cache.lower() in ("true", "1", "yes", "on")
    return bool(enable_cache)


def cache_control_view(
    timeout: int = 300,
    key_prefix: str = "view",
    vary_on_user: bool = True,
    vary_on_language: bool = True,
    cache_anonymous_only: bool = False,
):
    """
    Decorator for caching view responses that respects ENABLE_CACHE setting.

    Args:
        timeout: Cache timeout in seconds
        key_prefix: Cache key prefix
        vary_on_user: Whether to vary cache by user
        vary_on_language: Whether to vary cache by language
        cache_anonymous_only: Only cache for anonymous users

    Usage:
        @cache_control_view(timeout=600, key_prefix="landing")
        def get(self, request, *args, **kwargs):
            return Response(data)
    """

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(
            self, request: HttpRequest, *args, **kwargs
        ) -> Union[HttpResponse, Response]:

            if not is_cache_enabled():
                logger.debug(
                    f"Cache disabled - executing {view_func.__name__} without caching"
                )
                return view_func(self, request, *args, **kwargs)

            if cache_anonymous_only and request.user.is_authenticated:
                logger.debug(
                    f"Skipping cache for authenticated user in {view_func.__name__}"
                )
                return view_func(self, request, *args, **kwargs)

            cache_key_parts = [key_prefix, view_func.__name__]

            if vary_on_user:
                user_id = (
                    request.user.id if request.user.is_authenticated else "anonymous"
                )
                cache_key_parts.append(str(user_id))

            if vary_on_language:
                from django.utils import translation

                cache_key_parts.append(translation.get_language())

            if hasattr(request, "query_params"):

                query_string = request.query_params.urlencode()
            else:

                query_string = request.GET.urlencode()

            if query_string:
                cache_key_parts.append(query_string)

            cache_key = ":".join(cache_key_parts)

            try:
                cached_data = cache.get(cache_key)
                if cached_data is not None:
                    logger.debug(f"Cache hit for {cache_key}")

                    return Response(
                        cached_data["data"],
                        status=cached_data["status_code"],
                        headers=cached_data.get("headers", {}),
                    )
            except Exception as e:
                logger.warning(f"Cache get failed for {cache_key}: {e}")

            response = view_func(self, request, *args, **kwargs)

            try:

                if (
                    hasattr(response, "status_code")
                    and 200 <= response.status_code < 300
                ):

                    cache_data = {
                        "data": response.data if hasattr(response, "data") else None,
                        "status_code": response.status_code,
                        "headers": (
                            dict(response.items()) if hasattr(response, "items") else {}
                        ),
                    }
                    cache.set(cache_key, cache_data, timeout)
                    logger.debug(f"Cache set for {cache_key}")
            except Exception as e:
                logger.warning(f"Cache set failed for {cache_key}: {e}")

            return response

        return wrapper

    return decorator


def cache_control_method(
    timeout: int = 300, key_prefix: str = "method", vary_on_instance: bool = True
):
    """
    Decorator for caching method results that respects ENABLE_CACHE setting.

    Args:
        timeout: Cache timeout in seconds
        key_prefix: Cache key prefix
        vary_on_instance: Whether to include instance ID in cache key

    Usage:
        @cache_control_method(timeout=600, key_prefix="user_data")
        def get_user_data(self, user_id):
            return expensive_operation(user_id)
    """

    def decorator(method_func: Callable) -> Callable:
        @wraps(method_func)
        def wrapper(self, *args, **kwargs) -> Any:

            if not is_cache_enabled():
                logger.debug(
                    f"Cache disabled - executing {method_func.__name__} without caching"
                )
                return method_func(self, *args, **kwargs)

            cache_key_parts = [key_prefix, method_func.__name__]

            if vary_on_instance and hasattr(self, "id"):
                cache_key_parts.append(str(self.id))

            if args:
                cache_key_parts.extend(str(arg) for arg in args)

            if kwargs:
                cache_key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))

            cache_key = ":".join(cache_key_parts)

            try:
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached_result
            except Exception as e:
                logger.warning(f"Cache get failed for {cache_key}: {e}")

            result = method_func(self, *args, **kwargs)

            try:
                cache.set(cache_key, result, timeout)
                logger.debug(f"Cache set for {cache_key}")
            except Exception as e:
                logger.warning(f"Cache set failed for {cache_key}: {e}")

            return result

        return wrapper

    return decorator


def cache_control_function(timeout: int = 300, key_prefix: str = "function"):
    """
    Decorator for caching function results that respects ENABLE_CACHE setting.

    Args:
        timeout: Cache timeout in seconds
        key_prefix: Cache key prefix

    Usage:
        @cache_control_function(timeout=600, key_prefix="expensive_calc")
        def expensive_calculation(param1, param2):
            return complex_operation(param1, param2)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:

            if not is_cache_enabled():
                logger.debug(
                    f"Cache disabled - executing {func.__name__} without caching"
                )
                return func(*args, **kwargs)

            cache_key_parts = [key_prefix, func.__name__]

            if args:
                cache_key_parts.extend(str(arg) for arg in args)

            if kwargs:
                cache_key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))

            cache_key = ":".join(cache_key_parts)

            try:
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached_result
            except Exception as e:
                logger.warning(f"Cache get failed for {cache_key}: {e}")

            result = func(*args, **kwargs)

            try:
                cache.set(cache_key, result, timeout)
                logger.debug(f"Cache set for {cache_key}")
            except Exception as e:
                logger.warning(f"Cache set failed for {cache_key}: {e}")

            return result

        return wrapper

    return decorator


class CacheControlMixin:
    """
    Mixin for class-based views that provides cache control functionality.

    This mixin respects the ENABLE_CACHE setting and provides methods for
    caching view responses with proper key generation and invalidation.
    """

    cache_timeout: int = 300
    cache_key_prefix: str = "view"
    cache_vary_on_user: bool = True
    cache_vary_on_language: bool = True
    cache_anonymous_only: bool = False

    def get_cache_key(self, request: HttpRequest, *args, **kwargs) -> str:
        """
        Generate cache key for the current request.

        Args:
            request: HTTP request object
            *args: View arguments
            **kwargs: View keyword arguments

        Returns:
            str: Generated cache key
        """
        cache_key_parts = [self.cache_key_prefix, self.__class__.__name__]

        if self.cache_vary_on_user:
            user_id = request.user.id if request.user.is_authenticated else "anonymous"
            cache_key_parts.append(str(user_id))

        if self.cache_vary_on_language:
            from django.utils import translation

            cache_key_parts.append(translation.get_language())

        if hasattr(request, "query_params"):
            query_string = request.query_params.urlencode()
        else:
            query_string = request.GET.urlencode()

        if query_string:
            cache_key_parts.append(query_string)

        if args:
            cache_key_parts.extend(str(arg) for arg in args)

        if kwargs:
            cache_key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))

        return ":".join(cache_key_parts)

    def get_cached_response(
        self, request: HttpRequest, *args, **kwargs
    ) -> Optional[Union[HttpResponse, Response]]:
        """
        Get cached response if available and caching is enabled.

        Args:
            request: HTTP request object
            *args: View arguments
            **kwargs: View keyword arguments

        Returns:
            Cached response or None if not found/caching disabled
        """
        if not is_cache_enabled():
            return None

        if self.cache_anonymous_only and request.user.is_authenticated:
            return None

        cache_key = self.get_cache_key(request, *args, **kwargs)

        try:
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_response
        except Exception as e:
            logger.warning(f"Cache get failed for {cache_key}: {e}")

        return None

    def set_cached_response(
        self,
        request: HttpRequest,
        response: Union[HttpResponse, Response],
        *args,
        **kwargs,
    ) -> None:
        """
        Cache the response if caching is enabled and response is successful.

        Args:
            request: HTTP request object
            response: Response to cache
            *args: View arguments
            **kwargs: View keyword arguments
        """
        if not is_cache_enabled():
            return

        if self.cache_anonymous_only and request.user.is_authenticated:
            return

        if hasattr(response, "status_code") and not (200 <= response.status_code < 300):
            return

        cache_key = self.get_cache_key(request, *args, **kwargs)

        try:
            cache.set(cache_key, response, self.cache_timeout)
            logger.debug(f"Cache set for {cache_key}")
        except Exception as e:
            logger.warning(f"Cache set failed for {cache_key}: {e}")


def conditional_cache_page(timeout: int = 300, cache_anonymous_only: bool = False):
    """
    Conditional version of Django's cache_page decorator that respects ENABLE_CACHE.

    Args:
        timeout: Cache timeout in seconds
        cache_anonymous_only: Only cache for anonymous users

    Usage:
        @conditional_cache_page(timeout=600, cache_anonymous_only=True)
        def my_view(request):
            return HttpResponse("Hello")
    """

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:

            if not is_cache_enabled():
                logger.debug(
                    f"Cache disabled - executing {view_func.__name__} without page caching"
                )
                return view_func(request, *args, **kwargs)

            if cache_anonymous_only and request.user.is_authenticated:
                logger.debug(
                    f"Skipping page cache for authenticated user in {view_func.__name__}"
                )
                return view_func(request, *args, **kwargs)

            from django.views.decorators.cache import cache_page

            cached_view = cache_page(timeout)(view_func)
            return cached_view(request, *args, **kwargs)

        return wrapper

    return decorator


class ConditionalCachedProperty:
    """
    A cached property that respects the ENABLE_CACHE setting.

    When caching is disabled, this behaves like a regular property.
    When caching is enabled, it caches the result after first access.
    """

    def __init__(self, func: Callable):
        self.func = func
        self.attrname = None
        self.__doc__ = func.__doc__

    def __set_name__(self, owner, name):
        if self.attrname is None:
            self.attrname = name
        elif name != self.attrname:
            raise RuntimeError(
                f"Cannot assign the same ConditionalCachedProperty to two different names "
                f"({self.attrname!r} and {name!r})."
            )

    def __get__(self, instance, owner=None):
        if instance is None:
            return self

        if self.attrname is None:
            raise TypeError(
                "Cannot use ConditionalCachedProperty instance without calling __set_name__ on it."
            )

        if not is_cache_enabled():
            logger.debug(f"Cache disabled - computing {self.attrname} without caching")
            return self.func(instance)

        try:
            cache_attr = f"_cached_{self.attrname}"
            return getattr(instance, cache_attr)
        except AttributeError:

            value = self.func(instance)
            setattr(instance, cache_attr, value)
            logger.debug(f"Cached property {self.attrname} computed and cached")
            return value

    def __delete__(self, instance):
        if self.attrname is None:
            raise TypeError(
                "Cannot use ConditionalCachedProperty instance without calling __set_name__ on it."
            )

        cache_attr = f"_cached_{self.attrname}"
        try:
            delattr(instance, cache_attr)
            logger.debug(f"Cached property {self.attrname} cache cleared")
        except AttributeError:
            pass


cached_property = ConditionalCachedProperty
