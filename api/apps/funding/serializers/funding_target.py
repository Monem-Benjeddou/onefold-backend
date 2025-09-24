from rest_framework import serializers
from apps.funding.models import FundingTarget


class FundingTargetSerializer(serializers.ModelSerializer):
    """Serializer for FundingTarget model."""
    
    startup_name = serializers.CharField(source='startup.startup_name', read_only=True)
    target_amount_formatted = serializers.ReadOnlyField()
    pre_money_valuation_formatted = serializers.ReadOnlyField()
    post_money_valuation_formatted = serializers.ReadOnlyField()
    
    class Meta:
        model = FundingTarget
        fields = [
            'id', 'startup', 'startup_name', 'target_amount', 'target_amount_formatted',
            'pre_money_valuation', 'pre_money_valuation_formatted', 'post_money_valuation',
            'post_money_valuation_formatted', 'funding_round', 'use_of_funds', 'timeline',
            'is_active', 'created', 'updated'
        ]
        read_only_fields = ['id', 'post_money_valuation', 'created', 'updated']


class FundingTargetCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating FundingTarget records."""
    
    class Meta:
        model = FundingTarget
        fields = [
            'startup', 'target_amount', 'pre_money_valuation', 'funding_round',
            'use_of_funds', 'timeline', 'is_active'
        ]
    
    def validate(self, data):
        """Validate funding target data."""
        startup = data.get('startup')
        

        if startup and hasattr(startup, 'funding_target'):
            raise serializers.ValidationError(
                "This startup already has a funding target."
            )
        
        return data


class FundingTargetUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating FundingTarget records."""
    
    class Meta:
        model = FundingTarget
        fields = [
            'target_amount', 'pre_money_valuation', 'funding_round',
            'use_of_funds', 'timeline', 'is_active'
        ]
