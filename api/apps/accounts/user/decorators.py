from ast import boolop
from ctypes import Union
from functools import wraps
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _

from rest_framework import status

from apps.accounts.user.models import User


def is_user_exists(user_id_param=None, email_param=None):
    """
    Check if user exists
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if user_id_param is not None:
                user_id = kwargs.get(user_id_param)
                user_exists = User.objects.filter(id=user_id).exists()
            elif email_param is not None:
                email = request.request.data.get(email_param)
                user_exists = User.objects.filter(email=email).exists()

            if not user_exists:
                return Response(
                    {"error": _("User does not exist")},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
