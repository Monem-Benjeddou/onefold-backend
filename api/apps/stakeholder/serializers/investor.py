from rest_framework import serializers
from apps.stakeholder.models import Investor


class InvestorSerializer(serializers.ModelSerializer):
    """Serializer for Investor model."""
    
    startup_name = serializers.CharField(source='startup.startup_name', read_only=True)
    investment_amount_formatted = serializers.ReadOnlyField()
    
    class Meta:
        model = Investor
        fields = [
            'id', 'startup', 'startup_name', 'person_company_name', 'address',
            'contact_email', 'contact_phone', 'website', 'equity_percentage',
            'investment_type', 'investment_amount', 'investment_amount_formatted',
            'investment_date', 'is_lead_investor', 'board_seat', 'description',
            'is_active', 'created', 'updated'
        ]
        read_only_fields = ['id', 'created', 'updated']


class InvestorCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Investor records."""
    
    class Meta:
        model = Investor
        fields = [
            'startup', 'person_company_name', 'address', 'contact_email',
            'contact_phone', 'website', 'equity_percentage', 'investment_type',
            'investment_amount', 'investment_date', 'is_lead_investor', 'board_seat',
            'description', 'is_active'
        ]


class InvestorUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Investor records."""
    
    class Meta:
        model = Investor
        fields = [
            'person_company_name', 'address', 'contact_email', 'contact_phone',
            'website', 'equity_percentage', 'investment_type', 'investment_amount',
            'investment_date', 'is_lead_investor', 'board_seat', 'description', 'is_active'
        ]
