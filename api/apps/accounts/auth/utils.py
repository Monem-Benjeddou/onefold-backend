from functools import wraps
import re
from rest_framework.response import Response
from rest_framework import status
from django.utils.translation import gettext_lazy as _
from typing import List
from django.conf import settings
import traceback
import logging
from apps.accounts.user.models import User
import random


logger = logging.getLogger(__name__)


def generate_otp():
    """
    Generate a 6-digit numeric OTP code.
    Returns a string containing exactly 6 digits (0-9).
    """
    return "".join(random.choices("0123456789", k=6))


def user_with_this_email_should_exist(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        request = args[1]
        email = request.data.get("email")
        user = User.objects.filter(email=email).first()
        if not user:
            return Response(
                {"error": {"email": _("User with this email does not exist")}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return func(*args, **kwargs)

    return wrapper
