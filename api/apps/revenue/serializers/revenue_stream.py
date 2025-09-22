from rest_framework import serializers
from apps.revenue.models import RevenueStream


class RevenueStreamSerializer(serializers.ModelSerializer):
    """Serializer for RevenueStream model."""
    
    startup_name = serializers.CharField(source='startup.startup_name', read_only=True)
    monthly_revenue_formatted = serializers.ReadOnlyField()
    annual_revenue_formatted = serializers.ReadOnlyField()
    
    class Meta:
        model = RevenueStream
        fields = [
            'id', 'startup', 'startup_name', 'name', 'description', 'monthly_revenue',
            'monthly_revenue_formatted', 'annual_revenue', 'annual_revenue_formatted',
            'revenue_percentage', 'is_recurring', 'is_active', 'start_date', 'end_date',
            'created', 'updated'
        ]
        read_only_fields = ['id', 'created', 'updated']


class RevenueStreamCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating RevenueStream records."""
    
    class Meta:
        model = RevenueStream
        fields = [
            'startup', 'name', 'description', 'monthly_revenue', 'annual_revenue',
            'revenue_percentage', 'is_recurring', 'is_active', 'start_date', 'end_date'
        ]
    
    def validate(self, data):
        """Validate revenue stream data."""
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError(
                    "Start date cannot be after end date."
                )
        
        return data


class RevenueStreamUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating RevenueStream records."""
    
    class Meta:
        model = RevenueStream
        fields = [
            'name', 'description', 'monthly_revenue', 'annual_revenue',
            'revenue_percentage', 'is_recurring', 'is_active', 'start_date', 'end_date'
        ]
    
    def validate(self, data):
        """Validate revenue stream data."""
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError(
                    "Start date cannot be after end date."
                )
        
        return data
