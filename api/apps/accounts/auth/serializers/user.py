from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema_field
from apps.accounts.user.models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information.
    """
    
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'fullname', 'full_name',
            'created', 'updated', 'is_active', 'is_staff', 'is_superuser',
            'is_email_verified', 'is_verified', 'avatar', 'phone_number',
            'is_phone_verified', 'date_of_birth', 'gender', 'role'
        )
        read_only_fields = ('id', 'username', 'created', 'updated', 'is_active', 'is_staff', 'is_superuser')
        # Explicitly exclude problematic ManyToManyField relationships
        exclude = ('groups', 'user_permissions')
    
    @extend_schema_field(serializers.CharField)
    def get_full_name(self, obj) -> str:
        """
        Get user's full name.
        """
        return obj.fullname or obj.username
