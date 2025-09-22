from rest_framework import serializers
from apps.accounts.founder.models import PreviousCompany


class PreviousCompanySerializer(serializers.ModelSerializer):
    """Serializer for PreviousCompany model."""
    
    founder_name = serializers.CharField(source='founder.full_name', read_only=True)
    duration = serializers.ReadOnlyField()
    is_completed = serializers.ReadOnlyField()
    
    class Meta:
        model = PreviousCompany
        fields = [
            'id', 'founder', 'founder_name', 'company_name', 'profile_link',
            'position', 'start_date', 'end_date', 'is_current', 'description',
            'company_type', 'industry', 'company_size', 'duration', 'is_completed',
            'created', 'updated'
        ]
        read_only_fields = ['id', 'created', 'updated']


class PreviousCompanyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating PreviousCompany records."""
    
    class Meta:
        model = PreviousCompany
        fields = [
            'founder', 'company_name', 'profile_link', 'position', 'start_date',
            'end_date', 'is_current', 'description', 'company_type', 'industry',
            'company_size'
        ]
    
    def validate(self, data):
        """Validate company data."""
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError(
                    "Start date cannot be after end date."
                )
        
        if data.get('is_current') and data.get('end_date'):
            raise serializers.ValidationError(
                "Cannot have end date if currently working there."
            )
        
        return data


class PreviousCompanyUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating PreviousCompany records."""
    
    class Meta:
        model = PreviousCompany
        fields = [
            'company_name', 'profile_link', 'position', 'start_date', 'end_date',
            'is_current', 'description', 'company_type', 'industry', 'company_size'
        ]
    
    def validate(self, data):
        """Validate company data."""
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError(
                    "Start date cannot be after end date."
                )
        
        if data.get('is_current') and data.get('end_date'):
            raise serializers.ValidationError(
                "Cannot have end date if currently working there."
            )
        
        return data
