from rest_framework import serializers
from apps.accounts.founder.models import Education


class EducationSerializer(serializers.ModelSerializer):
    """Serializer for Education model."""
    
    founder_name = serializers.CharField(source='founder.full_name', read_only=True)
    duration = serializers.ReadOnlyField()
    is_completed = serializers.ReadOnlyField()
    
    class Meta:
        model = Education
        fields = [
            'id', 'founder', 'founder_name', 'institution_name', 'degree', 
            'field_of_study', 'start_date', 'end_date', 'is_current', 'gpa',
            'description', 'institution_website', 'duration', 'is_completed',
            'created', 'updated'
        ]
        read_only_fields = ['id', 'created', 'updated']


class EducationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Education records."""
    
    class Meta:
        model = Education
        fields = [
            'founder', 'institution_name', 'degree', 'field_of_study',
            'start_date', 'end_date', 'is_current', 'gpa', 'description',
            'institution_website'
        ]
    
    def validate(self, data):
        """Validate education data."""
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError(
                    "Start date cannot be after end date."
                )
        
        if data.get('is_current') and data.get('end_date'):
            raise serializers.ValidationError(
                "Cannot have end date if currently enrolled."
            )
        
        return data


class EducationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Education records."""
    
    class Meta:
        model = Education
        fields = [
            'institution_name', 'degree', 'field_of_study', 'start_date',
            'end_date', 'is_current', 'gpa', 'description', 'institution_website'
        ]
    
    def validate(self, data):
        """Validate education data."""
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError(
                    "Start date cannot be after end date."
                )
        
        if data.get('is_current') and data.get('end_date'):
            raise serializers.ValidationError(
                "Cannot have end date if currently enrolled."
            )
        
        return data
