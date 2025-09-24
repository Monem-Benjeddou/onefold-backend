"""
Tests for company app models.
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.company.models import (
    StartupProfile,
    StartupServiceProduct,
    DevelopmentStage,
    StartupDevelopmentStage,
    TargetedMarket,
    CompanyMember
)


class TestStartupProfile:
    """Test cases for StartupProfile model."""

    @pytest.mark.django_db
    def test_startup_profile_creation(self, user):
        """Test basic startup profile creation."""
        startup = StartupProfile.objects.create(
            startup_name="Test Startup",
            startup_industry="Technology",
            location="San Francisco, CA",
            founded_year=2020,
            primary_founder=user
        )

        assert startup.startup_name == "Test Startup"
        assert startup.startup_industry == "Technology"
        assert startup.location == "San Francisco, CA"
        assert startup.founded_year == 2020
        assert startup.primary_founder == user
        assert startup.is_verified is False
        assert startup.is_public is True
        assert startup.is_active is True

    @pytest.mark.django_db
    def test_startup_profile_string_representation(self, user):
        """Test startup profile string representation."""
        startup = StartupProfile.objects.create(
            startup_name="Test Startup",
            startup_industry="Technology",
            location="San Francisco, CA",
            founded_year=2020,
            primary_founder=user
        )

        assert str(startup) == "Test Startup (Technology)"

    @pytest.mark.django_db
    def test_startup_profile_social_links_property(self, user):
        """Test social_links property."""
        startup = StartupProfile.objects.create(
            startup_name="Test Startup",
            startup_industry="Technology",
            location="San Francisco, CA",
            founded_year=2020,
            linkedin_url="https://linkedin.com/company/test",
            twitter_url="https://twitter.com/test",
            primary_founder=user
        )

        social_links = startup.social_links
        assert social_links['linkedin'] == "https://linkedin.com/company/test"
        assert social_links['twitter'] == "https://twitter.com/test"
        assert social_links['facebook'] is None
        assert social_links['instagram'] is None
        assert social_links['youtube'] is None

    @pytest.mark.django_db
    def test_startup_profile_get_active_social_links(self, user):
        """Test get_active_social_links method."""
        startup = StartupProfile.objects.create(
            startup_name="Test Startup",
            startup_industry="Technology",
            location="San Francisco, CA",
            founded_year=2020,
            linkedin_url="https://linkedin.com/company/test",
            twitter_url="https://twitter.com/test",
            facebook_url="",
            primary_founder=user
        )

        active_links = startup.get_active_social_links()
        assert len(active_links) == 2
        assert 'linkedin' in active_links
        assert 'twitter' in active_links
        assert 'facebook' not in active_links

    @pytest.mark.django_db
    def test_startup_profile_age_years_property(self, user):
        """Test age_years property calculation."""
        from datetime import date
        current_year = date.today().year
        
        startup = StartupProfile.objects.create(
            startup_name="Test Startup",
            startup_industry="Technology",
            location="San Francisco, CA",
            founded_year=current_year - 5,
            primary_founder=user
        )

        assert startup.age_years == 5

    @pytest.mark.django_db
    def test_startup_profile_with_logo(self, user, test_image):
        """Test startup profile with logo upload."""
        startup = StartupProfile.objects.create(
            startup_name="Test Startup",
            startup_industry="Technology",
            location="San Francisco, CA",
            founded_year=2020,
            logo=test_image,
            primary_founder=user
        )

        assert startup.logo is not None
        assert "startups/" in startup.logo.url

    @pytest.mark.django_db
    def test_startup_profile_with_pitch_deck(self, user, test_pitch_deck):
        """Test startup profile with pitch deck upload."""
        startup = StartupProfile.objects.create(
            startup_name="Test Startup",
            startup_industry="Technology",
            location="San Francisco, CA",
            founded_year=2020,
            pitch_deck_file=test_pitch_deck,
            primary_founder=user
        )

        assert startup.pitch_deck_file is not None
        assert "startups/" in startup.pitch_deck_file.url

    @pytest.mark.django_db
    def test_startup_profile_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(IntegrityError):
            StartupProfile.objects.create(
                startup_name="Test Startup",

            )

    @pytest.mark.django_db
    def test_startup_profile_meta_options(self, user):
        """Test model meta options."""
        startup = StartupProfile.objects.create(
            startup_name="Test Startup",
            startup_industry="Technology",
            location="San Francisco, CA",
            founded_year=2020,
            primary_founder=user
        )

        assert startup._meta.verbose_name == "Startup Profile"
        assert startup._meta.verbose_name_plural == "Startup Profiles"
        assert startup._meta.db_table == "startup_profile"


class TestStartupServiceProduct:
    """Test cases for StartupServiceProduct model."""

    @pytest.mark.django_db
    def test_startup_service_product_creation(self, startup_profile):
        """Test basic startup service/product creation."""
        service = StartupServiceProduct.objects.create(
            startup=startup_profile,
            name="AI Analytics Platform",
            description="Advanced analytics solution",
            is_active=True
        )

        assert service.startup == startup_profile
        assert service.name == "AI Analytics Platform"
        assert service.description == "Advanced analytics solution"
        assert service.is_active is True

    @pytest.mark.django_db
    def test_startup_service_product_string_representation(self, startup_profile):
        """Test startup service/product string representation."""
        service = StartupServiceProduct.objects.create(
            startup=startup_profile,
            name="AI Analytics Platform",
            description="Advanced analytics solution"
        )

        expected = f"AI Analytics Platform ({startup_profile.startup_name})"
        assert str(service) == expected

    @pytest.mark.django_db
    def test_startup_service_product_defaults(self, startup_profile):
        """Test default values."""
        service = StartupServiceProduct.objects.create(
            startup=startup_profile,
            name="Test Service"
        )

        assert service.is_active is True
        assert service.description == ""

    @pytest.mark.django_db
    def test_startup_service_product_meta_options(self, startup_profile):
        """Test model meta options."""
        service = StartupServiceProduct.objects.create(
            startup=startup_profile,
            name="Test Service"
        )

        assert service._meta.verbose_name == "Startup Service/Product"
        assert service._meta.verbose_name_plural == "Startup Services/Products"
        assert service._meta.db_table == "startup_service_product"

    @pytest.mark.django_db
    def test_startup_service_product_related_name(self, startup_profile):
        """Test related name for startup relationship."""
        service1 = StartupServiceProduct.objects.create(
            startup=startup_profile,
            name="Service 1"
        )
        service2 = StartupServiceProduct.objects.create(
            startup=startup_profile,
            name="Service 2"
        )

        services = startup_profile.services_and_products.all()
        assert service1 in services
        assert service2 in services
        assert services.count() == 2


class TestDevelopmentStage:
    """Test cases for DevelopmentStage model."""

    @pytest.mark.django_db
    def test_development_stage_creation(self):
        """Test basic development stage creation."""
        stage = DevelopmentStage.objects.create(
            name="MVP",
            description="Minimum Viable Product",
            order=1
        )

        assert stage.name == "MVP"
        assert stage.description == "Minimum Viable Product"
        assert stage.order == 1

    @pytest.mark.django_db
    def test_development_stage_string_representation(self):
        """Test development stage string representation."""
        stage = DevelopmentStage.objects.create(
            name="MVP",
            description="Minimum Viable Product",
            order=1
        )

        assert str(stage) == "MVP"

    @pytest.mark.django_db
    def test_development_stage_meta_options(self):
        """Test model meta options."""
        stage = DevelopmentStage.objects.create(
            name="MVP",
            description="Minimum Viable Product",
            order=1
        )

        assert stage._meta.verbose_name == "Development Stage"
        assert stage._meta.verbose_name_plural == "Development Stages"


class TestStartupDevelopmentStage:
    """Test cases for StartupDevelopmentStage model."""

    @pytest.mark.django_db
    def test_startup_development_stage_creation(self, startup_profile, development_stage):
        """Test basic startup development stage creation."""
        startup_stage = StartupDevelopmentStage.objects.create(
            startup=startup_profile,
            stage=development_stage,
            notes="Currently working on MVP"
        )

        assert startup_stage.startup == startup_profile
        assert startup_stage.stage == development_stage

        assert startup_stage.assigned_date is not None
        assert startup_stage.notes == "Currently working on MVP"

    @pytest.mark.django_db
    def test_startup_development_stage_string_representation(self, startup_profile, development_stage):
        """Test startup development stage string representation."""
        startup_stage = StartupDevelopmentStage.objects.create(
            startup=startup_profile,
            stage=development_stage,
        )

        expected = f"{startup_profile.startup_name} - {development_stage.name}"
        assert str(startup_stage) == expected

    @pytest.mark.django_db
    def test_startup_development_stage_meta_options(self, startup_profile, development_stage):
        """Test model meta options."""
        startup_stage = StartupDevelopmentStage.objects.create(
            startup=startup_profile,
            stage=development_stage,
            assigned_date="2023-01-01"
        )

        assert startup_stage._meta.verbose_name == "Startup Development Stage"
        assert startup_stage._meta.verbose_name_plural == "Startup Development Stages"


class TestTargetedMarket:
    """Test cases for TargetedMarket model."""

    @pytest.mark.django_db
    @pytest.mark.django_db
    def test_targeted_market_creation(self, startup_profile):
        """Test basic targeted market creation."""
        market = TargetedMarket.objects.create(
            startup=startup_profile,
            market_name="SMEs",
            description="Small and medium enterprises",
            market_size=1000.00,
            market_share=5.00,
            market_type="local",
            is_primary=True
        )

        assert market.startup == startup_profile
        assert market.market_name == "SMEs"
        assert market.description == "Small and medium enterprises"
        assert market.market_size == 1000.00
        assert market.market_share == 5.00

    @pytest.mark.django_db
    @pytest.mark.django_db
    def test_targeted_market_string_representation(self, startup_profile):
        """Test targeted market string representation."""
        market = TargetedMarket.objects.create(
            startup=startup_profile,
            market_name="SMEs",
            description="Small and medium enterprises",
            market_size=1000.00,
            market_share=5.00,
            market_type="local",
            is_primary=True
        )


        expected = f"{startup_profile.startup_name} - SMEs (Local)"
        assert str(market) == expected

    @pytest.mark.django_db
    @pytest.mark.django_db
    def test_targeted_market_meta_options(self, startup_profile):
        """Test model meta options."""
        market = TargetedMarket.objects.create(
            startup=startup_profile,
            market_name="SMEs",
            description="Small and medium enterprises",
            market_size=1000.00,
            market_share=5.00,
            market_type="local",
            is_primary=True
        )

        assert market._meta.verbose_name == "Targeted Market"
        assert market._meta.verbose_name_plural == "Targeted Markets"


class TestCompanyMember:
    """Test cases for CompanyMember model."""

    @pytest.mark.django_db
    @pytest.mark.django_db
    def test_company_member_creation(self, startup_profile, user):
        """Test basic company member creation."""
        member = CompanyMember.objects.create(
            startup=startup_profile,
            user=user,
            member_type="founder",
            position="CEO",
            is_current=True,
            is_primary_contact=True
        )

        assert member.startup == startup_profile
        assert member.user == user
        assert member.member_type == "founder"
        assert member.position == "CEO"
        assert member.is_current is True
        assert member.is_primary_contact is True

    @pytest.mark.django_db
    @pytest.mark.django_db
    def test_company_member_string_representation(self, startup_profile, user):
        """Test company member string representation."""
        member = CompanyMember.objects.create(
            startup=startup_profile,
            user=user,
            member_type="founder",
            position="CEO"
        )


        expected = f"{user.fullname} - CEO at {startup_profile.startup_name}"
        assert str(member) == expected

    @pytest.mark.django_db
    @pytest.mark.django_db
    def test_company_member_choices(self, startup_profile, user):
        """Test member type choices."""
        valid_types = ['founder', 'co_founder', 'employee', 'advisor', 'consultant', 'intern', 'contractor']
        

        from apps.accounts.user.tests.factories import AnyUserFactory
        for member_type in valid_types:
            unique_user = AnyUserFactory()
            member = CompanyMember.objects.create(
                startup=startup_profile,
                user=unique_user,
                member_type=member_type,
                position="Test Position"
            )
            assert member.member_type == member_type

    @pytest.mark.django_db
    @pytest.mark.django_db
    def test_company_member_defaults(self, startup_profile, user):
        """Test default values."""
        member = CompanyMember.objects.create(
            startup=startup_profile,
            user=user,
            member_type="employee",
            position="Developer"
        )

        assert member.is_current is True
        assert member.is_primary_contact is False

    @pytest.mark.django_db
    @pytest.mark.django_db
    def test_company_member_meta_options(self, startup_profile, user):
        """Test model meta options."""
        member = CompanyMember.objects.create(
            startup=startup_profile,
            user=user,
            member_type="employee",
            position="Developer"
        )

        assert member._meta.verbose_name == "Company Member"
        assert member._meta.verbose_name_plural == "Company Members"
