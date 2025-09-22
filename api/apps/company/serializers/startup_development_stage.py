from rest_framework import serializers
from apps.company.models import StartupDevelopmentStage


class StartupDevelopmentStageSerializer(serializers.ModelSerializer):
    """Serializer for StartupDevelopmentStage model."""
    
    startup_name = serializers.CharField(source='startup.startup_name', read_only=True)
    stage_name = serializers.CharField(source='stage.name', read_only=True)
    
    class Meta:
        model = StartupDevelopmentStage
        fields = [
            'id', 'startup', 'startup_name', 'stage', 'stage_name',
            'assigned_date', 'notes', 'created', 'updated'
        ]
        read_only_fields = ['id', 'assigned_date', 'created', 'updated']


class StartupDevelopmentStageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating StartupDevelopmentStage records."""
    
    class Meta:
        model = StartupDevelopmentStage
        fields = ['startup', 'stage', 'notes']
    
    def validate(self, data):
        """Validate that startup doesn't already have a development stage."""
        startup = data.get('startup')
        if startup and hasattr(startup, 'development_stage'):
            raise serializers.ValidationError(
                "This startup already has a development stage assigned."
            )
        return data


class StartupDevelopmentStageUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating StartupDevelopmentStage records."""
    
    class Meta:
        model = StartupDevelopmentStage
        fields = ['stage', 'notes']
