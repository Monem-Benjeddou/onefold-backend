from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "name", "created"]
        read_only_fields = ["id", "email", "created"]


class MagicLinkRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class MagicLinkVerifySerializer(serializers.Serializer):
    token = serializers.CharField(max_length=200)
