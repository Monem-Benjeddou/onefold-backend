from rest_framework import serializers
from apps.funding.models import RaisedFund


class RaisedFundSerializer(serializers.ModelSerializer):
    """Serializer for RaisedFund model."""
    
    startup_name = serializers.CharField(source='startup.startup_name', read_only=True)
    amount_raised_formatted = serializers.ReadOnlyField()
    pre_money_valuation_formatted = serializers.ReadOnlyField()
    post_money_valuation_formatted = serializers.ReadOnlyField()
    
    class Meta:
        model = RaisedFund
        fields = [
            'id', 'startup', 'startup_name', 'amount_raised', 'amount_raised_formatted',
            'funding_round', 'funding_date', 'lead_investor', 'participating_investors',
            'pre_money_valuation', 'pre_money_valuation_formatted', 'post_money_valuation',
            'post_money_valuation_formatted', 'equity_offered', 'use_of_funds',
            'is_announced', 'announcement_date', 'description', 'created', 'updated'
        ]
        read_only_fields = ['id', 'post_money_valuation', 'created', 'updated']


class RaisedFundCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating RaisedFund records."""
    
    class Meta:
        model = RaisedFund
        fields = [
            'startup', 'amount_raised', 'funding_round', 'funding_date', 'lead_investor',
            'participating_investors', 'pre_money_valuation', 'equity_offered',
            'use_of_funds', 'is_announced', 'announcement_date', 'description'
        ]


class RaisedFundUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating RaisedFund records."""
    
    class Meta:
        model = RaisedFund
        fields = [
            'amount_raised', 'funding_round', 'funding_date', 'lead_investor',
            'participating_investors', 'pre_money_valuation', 'equity_offered',
            'use_of_funds', 'is_announced', 'announcement_date', 'description'
        ]
