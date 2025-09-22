"""
User Basic Serializer

Basic user information serializer for notifications.
Provides minimal user data needed for notification context.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """
    Basic user information for notifications.

    Provides essential user fields without sensitive information.
    All fields are read-only for security.
    """

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]
        read_only_fields = fields
