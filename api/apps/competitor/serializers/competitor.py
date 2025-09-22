from rest_framework import serializers
from apps.competitor.models import Competitor


class CompetitorSerializer(serializers.ModelSerializer):
    """Serializer for Competitor model."""
    
    startup_name = serializers.CharField(source='startup.startup_name', read_only=True)
    funding_raised_formatted = serializers.ReadOnlyField()
    age_years = serializers.ReadOnlyField()
    
    class Meta:
        model = Competitor
        fields = [
            'id', 'startup', 'startup_name', 'competitor_type', 'competitor_name',
            'competitor_url', 'description', 'market_share', 'funding_raised',
            'funding_raised_formatted', 'founded_year', 'age_years', 'employee_count',
            'location', 'strengths', 'weaknesses', 'threat_level', 'is_active',
            'created', 'updated'
        ]
        read_only_fields = ['id', 'created', 'updated']


class CompetitorCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Competitor records."""
    
    class Meta:
        model = Competitor
        fields = [
            'startup', 'competitor_type', 'competitor_name', 'competitor_url',
            'description', 'market_share', 'funding_raised', 'founded_year',
            'employee_count', 'location', 'strengths', 'weaknesses', 'threat_level',
            'is_active'
        ]


class CompetitorUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Competitor records."""
    
    class Meta:
        model = Competitor
        fields = [
            'competitor_type', 'competitor_name', 'competitor_url', 'description',
            'market_share', 'funding_raised', 'founded_year', 'employee_count',
            'location', 'strengths', 'weaknesses', 'threat_level', 'is_active'
        ]
