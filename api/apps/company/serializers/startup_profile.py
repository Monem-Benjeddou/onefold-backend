from rest_framework import serializers
from apps.company.models import StartupProfile, CompanyMember, TargetedMarket, StartupDevelopmentStage
from apps.accounts.founder.models import FounderProfile


class CompanyMemberSerializer(serializers.ModelSerializer):
    """Serializer for CompanyMember model (nested in startup profile)."""
    
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = CompanyMember
        fields = [
            'id', 'user', 'user_name', 'user_email', 'member_type', 'position',
            'start_date', 'end_date', 'is_current', 'is_primary_contact',
            'equity_percentage', 'description'
        ]
        read_only_fields = ['id']


class TargetedMarketSerializer(serializers.ModelSerializer):
    """Serializer for TargetedMarket model (nested in startup profile)."""
    
    class Meta:
        model = TargetedMarket
        fields = [
            'id', 'market_type', 'market_name', 'market_size', 'market_share',
            'description', 'is_primary'
        ]
        read_only_fields = ['id']


class StartupDevelopmentStageSerializer(serializers.ModelSerializer):
    """Serializer for StartupDevelopmentStage model (nested in startup profile)."""
    
    stage_name = serializers.CharField(source='stage.name', read_only=True)
    
    class Meta:
        model = StartupDevelopmentStage
        fields = [
            'id', 'stage', 'stage_name', 'assigned_date', 'notes'
        ]
        read_only_fields = ['id']


class StartupProfileSerializer(serializers.ModelSerializer):
    """Complete serializer for StartupProfile with nested relationships."""
    
    primary_founder_name = serializers.CharField(source='primary_founder.full_name', read_only=True)
    primary_founder_id = serializers.IntegerField(source='primary_founder.id', read_only=True)
    members = CompanyMemberSerializer(many=True, read_only=True)
    targeted_markets = TargetedMarketSerializer(many=True, read_only=True)
    development_stage = StartupDevelopmentStageSerializer(read_only=True)
    
    class Meta:
        model = StartupProfile
        fields = [
            'id', 'startup_name', 'startup_industry', 'website_link', 'location',
            'founded_year', 'bio', 'services_and_products', 'linkedin_url',
            'twitter_url', 'facebook_url', 'instagram_url', 'youtube_url',
            'logo', 'pitch_deck_link', 'pitch_deck_file', 'is_verified',
            'is_public', 'is_active', 'primary_founder', 'primary_founder_name',
            'primary_founder_id', 'members', 'targeted_markets', 'development_stage',
            'created', 'updated'
        ]
        read_only_fields = ['id', 'created', 'updated']


class StartupProfileCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating StartupProfile."""
    
    members = CompanyMemberSerializer(many=True, required=False)
    targeted_markets = TargetedMarketSerializer(many=True, required=False)
    
    class Meta:
        model = StartupProfile
        fields = [
            'startup_name', 'startup_industry', 'website_link', 'location',
            'founded_year', 'bio', 'services_and_products', 'linkedin_url',
            'twitter_url', 'facebook_url', 'instagram_url', 'youtube_url',
            'logo', 'pitch_deck_link', 'pitch_deck_file', 'is_verified',
            'is_public', 'is_active', 'primary_founder', 'members', 'targeted_markets'
        ]
    
    def create(self, validated_data):
        """Create startup profile with nested member and market data."""
        members_data = validated_data.pop('members', [])
        markets_data = validated_data.pop('targeted_markets', [])
        
        # Set primary founder if not provided
        if 'primary_founder' not in validated_data:
            user = self.context['request'].user
            try:
                founder_profile = user.founder_profile
                validated_data['primary_founder'] = user
            except FounderProfile.DoesNotExist:
                pass
        
        startup_profile = StartupProfile.objects.create(**validated_data)
        
        # Create company members
        for member in members_data:
            CompanyMember.objects.create(startup=startup_profile, **member)
        
        # Create targeted markets
        for market in markets_data:
            TargetedMarket.objects.create(startup=startup_profile, **market)
        
        return startup_profile


class StartupProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating StartupProfile."""
    
    members = CompanyMemberSerializer(many=True, required=False)
    targeted_markets = TargetedMarketSerializer(many=True, required=False)
    
    class Meta:
        model = StartupProfile
        fields = [
            'startup_name', 'startup_industry', 'website_link', 'location',
            'founded_year', 'bio', 'services_and_products', 'linkedin_url',
            'twitter_url', 'facebook_url', 'instagram_url', 'youtube_url',
            'logo', 'pitch_deck_link', 'pitch_deck_file', 'is_verified',
            'is_public', 'is_active', 'primary_founder', 'members', 'targeted_markets'
        ]
    
    def update(self, instance, validated_data):
        """Update startup profile with nested member and market data."""
        members_data = validated_data.pop('members', None)
        markets_data = validated_data.pop('targeted_markets', None)
        
        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update members if provided
        if members_data is not None:
            # Delete existing members
            instance.members.all().delete()
            # Create new ones
            for member in members_data:
                CompanyMember.objects.create(startup=instance, **member)
        
        # Update targeted markets if provided
        if markets_data is not None:
            # Delete existing markets
            instance.targeted_markets.all().delete()
            # Create new ones
            for market in markets_data:
                TargetedMarket.objects.create(startup=instance, **market)
        
        return instance
