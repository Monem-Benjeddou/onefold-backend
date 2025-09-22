from rest_framework import serializers
from apps.company.models import TargetedMarket


class TargetedMarketSerializer(serializers.ModelSerializer):
    """Serializer for TargetedMarket model."""
    
    startup_name = serializers.CharField(source='startup.startup_name', read_only=True)
    
    class Meta:
        model = TargetedMarket
        fields = [
            'id', 'startup', 'startup_name', 'market_type', 'market_name',
            'market_size', 'market_share', 'description', 'is_primary',
            'created', 'updated'
        ]
        read_only_fields = ['id', 'created', 'updated']


class TargetedMarketCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating TargetedMarket records."""
    
    class Meta:
        model = TargetedMarket
        fields = [
            'startup', 'market_type', 'market_name', 'market_size',
            'market_share', 'description', 'is_primary'
        ]
    
    def validate(self, data):
        """Validate market data."""
        startup = data.get('startup')
        is_primary = data.get('is_primary', False)
        
        # If setting as primary, ensure no other primary exists for this startup
        if is_primary and startup:
            if TargetedMarket.objects.filter(startup=startup, is_primary=True).exists():
                raise serializers.ValidationError(
                    "This startup already has a primary target market."
                )
        
        return data


class TargetedMarketUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating TargetedMarket records."""
    
    class Meta:
        model = TargetedMarket
        fields = [
            'market_type', 'market_name', 'market_size', 'market_share',
            'description', 'is_primary'
        ]
    
    def validate(self, data):
        """Validate market data."""
        is_primary = data.get('is_primary', False)
        
        # If setting as primary, ensure no other primary exists for this startup
        if is_primary and self.instance:
            if TargetedMarket.objects.filter(
                startup=self.instance.startup, 
                is_primary=True
            ).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(
                    "This startup already has a primary target market."
                )
        
        return data
