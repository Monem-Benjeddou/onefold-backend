from rest_framework import serializers

from .models import PrivacyPolicyPoint


class PrivacyPolicyPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivacyPolicyPoint
        fields = ["id", "_id", "title", "content", "order"]
