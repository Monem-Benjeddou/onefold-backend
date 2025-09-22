from rest_framework import serializers

from core.models.common import Image


class ListImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField()

    class Meta:
        model = Image
        fields = "__all__"
        read_only_fields = ["created", "updated"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["image"] = instance.image.url
        return data
