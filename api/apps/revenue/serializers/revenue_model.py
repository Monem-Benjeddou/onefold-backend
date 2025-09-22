from rest_framework import serializers
from apps.revenue.models import RevenueModel, StartupRevenueModel


class StartupRevenueModelSerializer(serializers.ModelSerializer):
    """Serializer for StartupRevenueModel (nested in revenue model)."""
    
    startup_name = serializers.CharField(source='startup.startup_name', read_only=True)
    
    class Meta:
        model = StartupRevenueModel
        fields = [
            'id', 'startup', 'startup_name', 'is_primary', 'percentage', 'description'
        ]
        read_only_fields = ['id']


class RevenueModelSerializer(serializers.ModelSerializer):
    """Serializer for RevenueModel model."""
    
    startup_revenue_models = StartupRevenueModelSerializer(many=True, read_only=True)
    
    class Meta:
        model = RevenueModel
        fields = [
            'id', 'name', 'description', 'order', 'is_active', 'startup_revenue_models',
            'created', 'updated'
        ]
        read_only_fields = ['id', 'created', 'updated']


class RevenueModelCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating RevenueModel records."""
    
    class Meta:
        model = RevenueModel
        fields = ['name', 'description', 'order', 'is_active']
    
    def validate_name(self, value):
        """Validate that name is unique."""
        if RevenueModel.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError(
                "A revenue model with this name already exists."
            )
        return value


class RevenueModelUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating RevenueModel records."""
    
    class Meta:
        model = RevenueModel
        fields = ['name', 'description', 'order', 'is_active']
    
    def validate_name(self, value):
        """Validate that name is unique (excluding current instance)."""
        if RevenueModel.objects.filter(name__iexact=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError(
                "A revenue model with this name already exists."
            )
        return value


class StartupRevenueModelCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating StartupRevenueModel records."""
    
    class Meta:
        model = StartupRevenueModel
        fields = ['startup', 'revenue_model', 'is_primary', 'percentage', 'description']
    
    def validate(self, data):
        """Validate startup revenue model data."""
        startup = data.get('startup')
        is_primary = data.get('is_primary', False)
        

        if is_primary and startup:
            if StartupRevenueModel.objects.filter(startup=startup, is_primary=True).exists():
                raise serializers.ValidationError(
                    "This startup already has a primary revenue model."
                )
        
        return data


class StartupRevenueModelUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating StartupRevenueModel records."""
    
    class Meta:
        model = StartupRevenueModel
        fields = ['is_primary', 'percentage', 'description']
    
    def validate(self, data):
        """Validate startup revenue model data."""
        is_primary = data.get('is_primary', False)
        

        if is_primary and self.instance:
            if StartupRevenueModel.objects.filter(
                startup=self.instance.startup, 
                is_primary=True
            ).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(
                    "This startup already has a primary revenue model."
                )
        
        return data
