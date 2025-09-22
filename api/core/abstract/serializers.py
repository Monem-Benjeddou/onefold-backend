from rest_framework import serializers
import uuid


class SafeUUIDField(serializers.UUIDField):
    """Custom UUID field that handles both UUID objects and string representations"""

    def to_representation(self, value):
        if value is None:
            return None

        if isinstance(value, uuid.UUID):
            return super().to_representation(value)

        if isinstance(value, str):
            try:
                uuid_obj = uuid.UUID(value)
                return super().to_representation(uuid_obj)
            except (ValueError, TypeError):

                return value

        try:
            str_value = str(value)
            uuid_obj = uuid.UUID(str_value)
            return super().to_representation(uuid_obj)
        except (ValueError, TypeError):
            return str(value)


class AbstractSerializer(serializers.ModelSerializer):
    id = SafeUUIDField(read_only=True)
    created = serializers.DateTimeField(read_only=True)
    updated = serializers.DateTimeField(read_only=True)

    class Meta:
        abstract = True
        fields = [
            "id",
            "created",
            "updated",
        ]
        read_only_fields = [
            "id",
            "created",
            "updated",
        ]

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        return rep
