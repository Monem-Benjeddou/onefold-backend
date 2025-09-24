from rest_framework import serializers
from apps.company.models import StartupProfile, CompanyMember, TargetedMarket, StartupDevelopmentStage, StartupServiceProduct
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
            'id', 'startup', 'stage', 'stage_name', 'assigned_date', 'notes'
        ]
        read_only_fields = ['id']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Normalize UUIDs to strings for stable test expectations
        data['id'] = str(instance.id)
        data['startup'] = str(instance.startup_id) if getattr(instance, 'startup_id', None) else data.get('startup')
        data['stage'] = str(instance.stage_id) if getattr(instance, 'stage_id', None) else data.get('stage')
        return data


class StartupServiceProductSerializer(serializers.ModelSerializer):
    # When used nested under StartupProfile create/update, startup is provided by parent
    startup = serializers.PrimaryKeyRelatedField(
        queryset=StartupProfile.objects.all(),
        help_text="ID of the startup this service/product belongs to",
        required=False,
        allow_null=True,
    )
    
    class Meta:
        model = StartupServiceProduct
        fields = ["id", "startup", "name", "description", "is_active"]
        read_only_fields = ["id"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['id'] = str(instance.id)
        data['startup'] = str(instance.startup_id) if getattr(instance, 'startup_id', None) else data.get('startup')
        return data


class StartupProfileSerializer(serializers.ModelSerializer):
    """Complete serializer for StartupProfile with nested relationships."""
    
    primary_founder_name = serializers.CharField(source='primary_founder.full_name', read_only=True)
    primary_founder_id = serializers.IntegerField(source='primary_founder.id', read_only=True)
    members = CompanyMemberSerializer(many=True, read_only=True)
    services_and_products = StartupServiceProductSerializer(many=True, read_only=True)
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
    services_and_products = StartupServiceProductSerializer(many=True, required=False)

    website_link = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    linkedin_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    twitter_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    facebook_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    instagram_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    youtube_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    pitch_deck_link = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    logo = serializers.ImageField(required=False, allow_null=True)
    pitch_deck_file = serializers.FileField(required=False, allow_null=True)
    
    class Meta:
        model = StartupProfile
        fields = [
            'startup_name', 'startup_industry', 'website_link', 'location',
            'founded_year', 'bio', 'services_and_products', 'linkedin_url',
            'twitter_url', 'facebook_url', 'instagram_url', 'youtube_url',
            'logo', 'pitch_deck_link', 'pitch_deck_file', 'is_verified',
            'is_public', 'is_active', 'primary_founder', 'members', 'targeted_markets', 'services_and_products'
        ]
    
    def create(self, validated_data):
        """Create startup profile with nested member and market data."""
        members_data = validated_data.pop('members', [])
        markets_data = validated_data.pop('targeted_markets', [])
        services_products_data = validated_data.pop('services_and_products', [])
        
        # Ensure creator is owner/primary founder
        if 'primary_founder' not in validated_data:
            user = self.context['request'].user
            validated_data['primary_founder'] = user

        # Normalize empty strings to None for optional fields
        optional_fields = [
            'website_link', 'linkedin_url', 'twitter_url', 'facebook_url',
            'instagram_url', 'youtube_url', 'pitch_deck_link', 'logo',
            'pitch_deck_file'
        ]
        for field_name in optional_fields:
            value = validated_data.get(field_name, None)
            if value == "":
                validated_data[field_name] = None
        
        startup_profile = StartupProfile.objects.create(**validated_data)
        
        # Create company members
        for member in members_data:
            CompanyMember.objects.create(startup=startup_profile, **member)
        
        # Create targeted markets
        for market in markets_data:
            TargetedMarket.objects.create(startup=startup_profile, **market)

        # Create services/products
        for item in services_products_data:
            StartupServiceProduct.objects.create(startup=startup_profile, **item)
        
        return startup_profile


class StartupProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating StartupProfile."""
    
    members = CompanyMemberSerializer(many=True, required=False)
    targeted_markets = TargetedMarketSerializer(many=True, required=False)
    services_and_products = StartupServiceProductSerializer(many=True, required=False)
    
    class Meta:
        model = StartupProfile
        fields = [
            'startup_name', 'startup_industry', 'website_link', 'location',
            'founded_year', 'bio', 'services_and_products', 'linkedin_url',
            'twitter_url', 'facebook_url', 'instagram_url', 'youtube_url',
            'logo', 'pitch_deck_link', 'pitch_deck_file', 'is_verified',
            'is_public', 'is_active', 'primary_founder', 'members', 'targeted_markets', 'services_and_products'
        ]
    
    def update(self, instance, validated_data):
        """Update startup profile with nested member and market data."""
        members_data = validated_data.pop('members', None)
        markets_data = validated_data.pop('targeted_markets', None)
        services_products_data = validated_data.pop('services_and_products', None)
        
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

        # Update services/products if provided
        if services_products_data is not None:
            instance.services_and_products.all().delete()
            for item in services_products_data:
                StartupServiceProduct.objects.create(startup=instance, **item)
        
        return instance
