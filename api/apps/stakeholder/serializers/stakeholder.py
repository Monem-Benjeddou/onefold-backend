from rest_framework import serializers
from apps.stakeholder.models import Stakeholder


class StakeholderSerializer(serializers.ModelSerializer):
    """Serializer for Stakeholder model."""
    
    startup_name = serializers.CharField(source='startup.startup_name', read_only=True)
    investment_amount_formatted = serializers.ReadOnlyField()
    
    class Meta:
        model = Stakeholder
        fields = [
            'id', 'startup', 'startup_name', 'full_name', 'stakeholder_type',
            'role_title', 'influence_level', 'stake_interest_level',
            'ownership_percentage', 'investment_amount', 'investment_amount_formatted',
            'contact_email', 'contact_phone', 'company_name', 'description',
            'is_active', 'created', 'updated'
        ]
        read_only_fields = ['id', 'created', 'updated']


class StakeholderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Stakeholder records."""
    
    class Meta:
        model = Stakeholder
        fields = [
            'startup', 'full_name', 'stakeholder_type', 'role_title',
            'influence_level', 'stake_interest_level', 'ownership_percentage',
            'investment_amount', 'contact_email', 'contact_phone', 'company_name',
            'description', 'is_active'
        ]


class StakeholderUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Stakeholder records."""
    
    class Meta:
        model = Stakeholder
        fields = [
            'full_name', 'stakeholder_type', 'role_title', 'influence_level',
            'stake_interest_level', 'ownership_percentage', 'investment_amount',
            'contact_email', 'contact_phone', 'company_name', 'description', 'is_active'
        ]
