from rest_framework import serializers
from apps.company.models import DevelopmentStage


class DevelopmentStageSerializer(serializers.ModelSerializer):
    """Serializer for DevelopmentStage model."""
    
    class Meta:
        model = DevelopmentStage
        fields = [
            'id', 'name', 'description', 'order', 'is_active', 'created', 'updated'
        ]
        read_only_fields = ['id', 'created', 'updated']


class DevelopmentStageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating DevelopmentStage records."""
    
    class Meta:
        model = DevelopmentStage
        fields = ['name', 'description', 'order', 'is_active']
    
    def validate_name(self, value):
        """Validate that name is unique."""
        if DevelopmentStage.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError(
                "A development stage with this name already exists."
            )
        return value


class DevelopmentStageUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating DevelopmentStage records."""
    
    class Meta:
        model = DevelopmentStage
        fields = ['name', 'description', 'order', 'is_active']
    
    def validate_name(self, value):
        """Validate that name is unique (excluding current instance)."""
        if DevelopmentStage.objects.filter(name__iexact=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError(
                "A development stage with this name already exists."
            )
        return value
