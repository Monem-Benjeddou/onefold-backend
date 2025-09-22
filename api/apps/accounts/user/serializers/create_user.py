from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.accounts.user.serializers.user import UserSerializer
from apps.accounts.user.models import User


class CreateUserSerializer(UserSerializer):
    avatar = serializers.ImageField(required=False)
    email = serializers.EmailField(required=True)
    fullname = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "fullname",
            "avatar",
            "phone_number",
            "role",
            "role_translated",
            "country",
            "country_name",
        ]
        read_only_fields = [
            "id",
            "country_name",
            "role_translated",
        ]

    def validate(self, attrs):

        if "email" not in attrs or not attrs["email"]:
            raise serializers.ValidationError(
                {"error": {"email": [_("Email is required.")]}}
            )

        if "fullname" not in attrs or not attrs["fullname"]:
            raise serializers.ValidationError(
                {"error": {"fullname": [_("Fullname is required.")]}}
            )

        return attrs

    def create(self, validated_data):
        fullname = validated_data.pop("fullname")
        username = fullname.replace(" ", "_").lower()
        if User.objects.filter(username=username).exists():
            username = f"{username}_{User.objects.count()}"
        user = User.objects.create(
            username=username, fullname=fullname, **validated_data
        )
        return user
