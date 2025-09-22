from rest_framework import serializers
from apps.accounts.founder.models import FounderProfile, Education, PreviousCompany
from apps.accounts.user.models import User


class EducationSerializer(serializers.ModelSerializer):
    """Serializer for Education model (nested in founder profile)."""
    
    class Meta:
        model = Education
        fields = [
            'id', 'institution_name', 'degree', 'field_of_study', 
            'start_date', 'end_date', 'is_current', 'gpa', 
            'description', 'institution_website'
        ]
        read_only_fields = ['id']


class PreviousCompanySerializer(serializers.ModelSerializer):
    """Serializer for PreviousCompany model (nested in founder profile)."""
    
    class Meta:
        model = PreviousCompany
        fields = [
            'id', 'company_name', 'profile_link', 'position', 
            'start_date', 'end_date', 'is_current', 'description',
            'company_type', 'industry', 'company_size'
        ]
        read_only_fields = ['id']


class FounderProfileSerializer(serializers.ModelSerializer):
    """Complete serializer for FounderProfile with nested relationships."""
    
    user = serializers.StringRelatedField(read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    education_history = EducationSerializer(many=True, read_only=True)
    previous_companies = PreviousCompanySerializer(many=True, read_only=True)
    social_links = serializers.ReadOnlyField()
    active_social_links = serializers.SerializerMethodField()
    
    class Meta:
        model = FounderProfile
        fields = [
            'id', 'user', 'user_id', 'full_name', 'email_address', 'role',
            'location', 'birthdate', 'linkedin_url', 'twitter_url', 
            'facebook_url', 'instagram_url', 'github_url', 'personal_website',
            'bio', 'avatar', 'background_image', 'is_verified', 'is_public',
            'social_links', 'active_social_links', 'education_history',
            'previous_companies', 'created', 'updated'
        ]
        read_only_fields = ['id', 'user', 'user_id', 'created', 'updated']
    
    def get_active_social_links(self, obj):
        """Return only non-empty social media links."""
        return obj.get_active_social_links()


class FounderProfileCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating FounderProfile."""
    
    education_history = EducationSerializer(many=True, required=False)
    previous_companies = PreviousCompanySerializer(many=True, required=False)
    
    class Meta:
        model = FounderProfile
        fields = [
            'full_name', 'email_address', 'role', 'location', 'birthdate',
            'linkedin_url', 'twitter_url', 'facebook_url', 'instagram_url',
            'github_url', 'personal_website', 'bio', 'avatar', 'background_image',
            'is_verified', 'is_public', 'education_history', 'previous_companies'
        ]
    
    def create(self, validated_data):
        """Create founder profile with nested education and company data."""
        education_data = validated_data.pop('education_history', [])
        companies_data = validated_data.pop('previous_companies', [])
        
        # Get user from context
        user = self.context['request'].user
        validated_data['user'] = user
        
        founder_profile = FounderProfile.objects.create(**validated_data)
        
        # Create education records
        for education in education_data:
            Education.objects.create(founder=founder_profile, **education)
        
        # Create previous company records
        for company in companies_data:
            PreviousCompany.objects.create(founder=founder_profile, **company)
        
        return founder_profile


class FounderProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating FounderProfile."""
    
    education_history = EducationSerializer(many=True, required=False)
    previous_companies = PreviousCompanySerializer(many=True, required=False)
    
    class Meta:
        model = FounderProfile
        fields = [
            'full_name', 'email_address', 'role', 'location', 'birthdate',
            'linkedin_url', 'twitter_url', 'facebook_url', 'instagram_url',
            'github_url', 'personal_website', 'bio', 'avatar', 'background_image',
            'is_verified', 'is_public', 'education_history', 'previous_companies'
        ]
    
    def update(self, instance, validated_data):
        """Update founder profile with nested education and company data."""
        education_data = validated_data.pop('education_history', None)
        companies_data = validated_data.pop('previous_companies', None)
        
        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update education history if provided
        if education_data is not None:
            # Delete existing education records
            instance.education_history.all().delete()
            # Create new ones
            for education in education_data:
                Education.objects.create(founder=instance, **education)
        
        # Update previous companies if provided
        if companies_data is not None:
            # Delete existing company records
            instance.previous_companies.all().delete()
            # Create new ones
            for company in companies_data:
                PreviousCompany.objects.create(founder=instance, **company)
        
        return instance
