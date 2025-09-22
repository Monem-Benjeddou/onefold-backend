"""
CSRF exemption decorators for API views.
"""

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from functools import wraps


def api_csrf_exempt(view_func):
    """
    Decorator to exempt API views from CSRF protection.
    """
    return csrf_exempt(view_func)


def api_csrf_exempt_method(cls):
    """
    Class decorator to exempt all methods of a view class from CSRF protection.
    """
    for attr_name in dir(cls):
        attr = getattr(cls, attr_name)
        if callable(attr) and not attr_name.startswith('_'):
            setattr(cls, attr_name, method_decorator(csrf_exempt)(attr))
    return cls
