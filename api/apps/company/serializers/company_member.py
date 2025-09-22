from rest_framework import serializers
from apps.company.models import CompanyMember


class CompanyMemberSerializer(serializers.ModelSerializer):
    """Serializer for CompanyMember model."""
    
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    startup_name = serializers.CharField(source='startup.startup_name', read_only=True)
    
    class Meta:
        model = CompanyMember
        fields = [
            'id', 'user', 'user_name', 'user_email', 'startup', 'startup_name',
            'member_type', 'position', 'start_date', 'end_date', 'is_current',
            'is_primary_contact', 'equity_percentage', 'description', 'created', 'updated'
        ]
        read_only_fields = ['id', 'created', 'updated']


class CompanyMemberCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating CompanyMember records."""
    
    class Meta:
        model = CompanyMember
        fields = [
            'user', 'startup', 'member_type', 'position', 'start_date',
            'end_date', 'is_current', 'is_primary_contact', 'equity_percentage',
            'description'
        ]
    
    def validate(self, data):
        """Validate member data."""
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError(
                    "Start date cannot be after end date."
                )
        
        if data.get('is_current') and data.get('end_date'):
            raise serializers.ValidationError(
                "Cannot have end date if currently a member."
            )
        
        # Check for duplicate user-startup combination
        user = data.get('user')
        startup = data.get('startup')
        if user and startup:
            if CompanyMember.objects.filter(user=user, startup=startup).exists():
                raise serializers.ValidationError(
                    "This user is already a member of this startup."
                )
        
        return data


class CompanyMemberUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating CompanyMember records."""
    
    class Meta:
        model = CompanyMember
        fields = [
            'member_type', 'position', 'start_date', 'end_date', 'is_current',
            'is_primary_contact', 'equity_percentage', 'description'
        ]
    
    def validate(self, data):
        """Validate member data."""
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError(
                    "Start date cannot be after end date."
                )
        
        if data.get('is_current') and data.get('end_date'):
            raise serializers.ValidationError(
                "Cannot have end date if currently a member."
            )
        
        return data
