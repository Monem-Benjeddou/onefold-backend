"""
Tests for company app serializers.
"""

import pytest
from rest_framework.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.company.serializers.startup_profile import (
    StartupProfileSerializer,
    StartupProfileCreateSerializer,
    StartupProfileUpdateSerializer,
    StartupServiceProductSerializer,
    StartupDevelopmentStageSerializer
)
from apps.company.serializers.development_stage import DevelopmentStageSerializer
from apps.company.serializers.targeted_market import TargetedMarketSerializer
from apps.company.serializers.company_member import CompanyMemberSerializer


class TestStartupProfileSerializer:
    """Test cases for StartupProfileSerializer."""

    @pytest.mark.django_db
    def test_startup_profile_serialization(self, startup_profile):
        """Test startup profile serialization."""
        serializer = StartupProfileSerializer(startup_profile)
        data = serializer.data

        assert data['id'] == str(startup_profile.id)
        assert data['startup_name'] == startup_profile.startup_name
        assert data['startup_industry'] == startup_profile.startup_industry
        assert data['website_link'] == startup_profile.website_link
        assert data['location'] == startup_profile.location
        assert data['founded_year'] == startup_profile.founded_year
        assert data['bio'] == startup_profile.bio
        assert data['is_verified'] == startup_profile.is_verified
        assert data['is_public'] == startup_profile.is_public
        assert data['is_active'] == startup_profile.is_active

    @pytest.mark.django_db
    def test_startup_profile_deserialization(self, user):
        """Test startup profile deserialization."""
        data = {
            'startup_name': 'New Startup',
            'startup_industry': 'Technology',
            'website_link': 'https://newstartup.com',
            'location': 'San Francisco, CA',
            'founded_year': 2023,
            'bio': 'A new startup',
            'linkedin_url': 'https://linkedin.com/company/newstartup',
            'is_verified': False,
            'is_public': True,
            'is_active': True,
            'primary_founder': user.id
        }

        serializer = StartupProfileSerializer(data=data)
        assert serializer.is_valid()
        startup = serializer.save()

        assert startup.startup_name == 'New Startup'
        assert startup.startup_industry == 'Technology'
        assert startup.website_link == 'https://newstartup.com'
        assert startup.location == 'San Francisco, CA'
        assert startup.founded_year == 2023
        assert startup.bio == 'A new startup'
        assert startup.linkedin_url == 'https://linkedin.com/company/newstartup'
        assert startup.is_verified is False
        assert startup.is_public is True
        assert startup.is_active is True
        assert startup.primary_founder == user

    @pytest.mark.django_db
    def test_startup_profile_validation_errors(self):
        """Test startup profile validation errors."""
        data = {
            'startup_name': '',
            'startup_industry': 'Technology',
            'location': 'San Francisco, CA',
            'founded_year': 2023
        }

        serializer = StartupProfileSerializer(data=data)
        assert not serializer.is_valid()
        assert 'startup_name' in serializer.errors

    @pytest.mark.django_db
    def test_startup_profile_read_only_fields(self, startup_profile):
        """Test that read-only fields are not writable."""
        data = {
            'id': 'new-id',
            'created': '2023-01-01T00:00:00Z',
            'updated': '2023-01-01T00:00:00Z',
            'startup_name': 'Updated Name'
        }

        serializer = StartupProfileSerializer(startup_profile, data=data, partial=True)
        assert serializer.is_valid()
        updated_startup = serializer.save()


        assert updated_startup.id == startup_profile.id
        assert updated_startup.created == startup_profile.created

        assert updated_startup.updated >= startup_profile.updated
        assert updated_startup.startup_name == 'Updated Name'


class TestStartupProfileCreateSerializer:
    """Test cases for StartupProfileCreateSerializer."""

    @pytest.mark.django_db
    def test_startup_profile_create_serialization(self, user):
        """Test startup profile creation serialization."""
        data = {
            'startup_name': 'New Startup',
            'startup_industry': 'Technology',
            'website_link': 'https://newstartup.com',
            'location': 'San Francisco, CA',
            'founded_year': 2023,
            'bio': 'A new startup',
            'primary_founder': user.id
        }

        serializer = StartupProfileCreateSerializer(data=data)
        assert serializer.is_valid()
        startup = serializer.save()

        assert startup.startup_name == 'New Startup'
        assert startup.startup_industry == 'Technology'
        assert startup.primary_founder == user

    @pytest.mark.django_db
    def test_startup_profile_create_with_services_products(self, user):
        """Test startup profile creation with services/products."""
        data = {
            'startup_name': 'New Startup',
            'startup_industry': 'Technology',
            'location': 'San Francisco, CA',
            'founded_year': 2023,
            'primary_founder': user.id,
            'services_and_products': [
                {
                    'name': 'Service 1',
                    'description': 'First service',
                    'is_active': True
                },
                {
                    'name': 'Service 2',
                    'description': 'Second service',
                    'is_active': True
                }
            ]
        }

        serializer = StartupProfileCreateSerializer(data=data)
        assert serializer.is_valid()
        startup = serializer.save()

        assert startup.startup_name == 'New Startup'
        assert startup.services_and_products.count() == 2
        assert startup.services_and_products.first().name == 'Service 1'
        assert startup.services_and_products.last().name == 'Service 2'


class TestStartupProfileUpdateSerializer:
    """Test cases for StartupProfileUpdateSerializer."""

    @pytest.mark.django_db
    def test_startup_profile_update_serialization(self, startup_profile):
        """Test startup profile update serialization."""
        data = {
            'startup_name': 'Updated Startup Name',
            'bio': 'Updated bio',
            'is_verified': True
        }

        serializer = StartupProfileUpdateSerializer(startup_profile, data=data, partial=True)
        assert serializer.is_valid()
        updated_startup = serializer.save()

        assert updated_startup.startup_name == 'Updated Startup Name'
        assert updated_startup.bio == 'Updated bio'
        assert updated_startup.is_verified is True

        assert updated_startup.startup_industry == startup_profile.startup_industry
        assert updated_startup.location == startup_profile.location


class TestStartupServiceProductSerializer:
    """Test cases for StartupServiceProductSerializer."""

    @pytest.mark.django_db
    def test_startup_service_product_serialization(self, startup_service_product):
        """Test startup service/product serialization."""
        serializer = StartupServiceProductSerializer(startup_service_product)
        data = serializer.data

        assert data['id'] == str(startup_service_product.id)
        assert data['startup'] == str(startup_service_product.startup.id)
        assert data['name'] == startup_service_product.name
        assert data['description'] == startup_service_product.description
        assert data['is_active'] == startup_service_product.is_active

    @pytest.mark.django_db
    def test_startup_service_product_deserialization(self, startup_profile):
        """Test startup service/product deserialization."""
        data = {
            'startup': startup_profile.id,
            'name': 'New Service',
            'description': 'A new service',
            'is_active': True
        }

        serializer = StartupServiceProductSerializer(data=data)
        assert serializer.is_valid()
        service = serializer.save()

        assert service.startup == startup_profile
        assert service.name == 'New Service'
        assert service.description == 'A new service'
        assert service.is_active is True

    def test_startup_service_product_validation_errors(self):
        """Test startup service/product validation errors."""
        data = {
            'startup': 'invalid-uuid',
            'name': '',
            'is_active': True
        }

        serializer = StartupServiceProductSerializer(data=data)
        assert not serializer.is_valid()
        assert 'startup' in serializer.errors
        assert 'name' in serializer.errors

    @pytest.mark.django_db
    def test_startup_service_product_read_only_fields(self, startup_service_product):
        """Test that read-only fields are not writable."""
        data = {
            'id': 'new-id',
            'name': 'Updated Service Name'
        }

        serializer = StartupServiceProductSerializer(startup_service_product, data=data, partial=True)
        assert serializer.is_valid()
        updated_service = serializer.save()


        assert updated_service.id == startup_service_product.id
        assert updated_service.name == 'Updated Service Name'


class TestDevelopmentStageSerializer:
    """Test cases for DevelopmentStageSerializer."""

    @pytest.mark.django_db
    def test_development_stage_serialization(self, development_stage):
        """Test development stage serialization."""
        serializer = DevelopmentStageSerializer(development_stage)
        data = serializer.data

        assert data['id'] == str(development_stage.id)
        assert data['name'] == development_stage.name
        assert data['description'] == development_stage.description
        assert data['order'] == development_stage.order

    @pytest.mark.django_db
    def test_development_stage_deserialization(self):
        """Test development stage deserialization."""
        data = {
            'name': 'Beta',
            'description': 'Beta testing stage',
            'order': 2
        }

        serializer = DevelopmentStageSerializer(data=data)
        assert serializer.is_valid()
        stage = serializer.save()

        assert stage.name == 'Beta'
        assert stage.description == 'Beta testing stage'
        assert stage.order == 2

    def test_development_stage_validation_errors(self):
        """Test development stage validation errors."""
        data = {
            'name': '',
            'description': 'Test description',
            'order': 'invalid'
        }

        serializer = DevelopmentStageSerializer(data=data)
        assert not serializer.is_valid()
        assert 'name' in serializer.errors
        assert 'order' in serializer.errors


class TestStartupDevelopmentStageSerializer:
    """Test cases for StartupDevelopmentStageSerializer."""

    @pytest.mark.django_db
    def test_startup_development_stage_serialization(self, startup_development_stage):
        """Test startup development stage serialization."""
        serializer = StartupDevelopmentStageSerializer(startup_development_stage)
        data = serializer.data

        assert data['id'] == str(startup_development_stage.id)
        assert data['stage'] == str(startup_development_stage.stage.id)
        assert data['stage_name'] == startup_development_stage.stage.name

        assert data['assigned_date'] == startup_development_stage.assigned_date.isoformat().replace('+00:00', 'Z')
        assert data['notes'] == startup_development_stage.notes

    @pytest.mark.django_db
    def test_startup_development_stage_deserialization(self, startup_profile, development_stage):
        """Test startup development stage deserialization."""
        data = {
            'startup': startup_profile.id,
            'stage': development_stage.id,
            'assigned_date': '2023-06-01',
            'notes': 'New notes'
        }

        serializer = StartupDevelopmentStageSerializer(data=data)
        assert serializer.is_valid()
        startup_stage = serializer.save()

        assert startup_stage.stage == development_stage
        assert startup_stage.assigned_date is not None
        assert startup_stage.notes == 'New notes'

    @pytest.mark.django_db
    def test_startup_development_stage_read_only_fields(self, startup_development_stage):
        """Test that read-only fields are not writable."""
        data = {
            'id': 'new-id',
            'stage_name': 'New Stage Name',
            'notes': 'Updated notes'
        }

        serializer = StartupDevelopmentStageSerializer(startup_development_stage, data=data, partial=True)
        assert serializer.is_valid()
        updated_stage = serializer.save()


        assert updated_stage.id == startup_development_stage.id
        assert updated_stage.stage.name == startup_development_stage.stage.name
        assert updated_stage.notes == 'Updated notes'


class TestTargetedMarketSerializer:
    """Test cases for TargetedMarketSerializer."""

    @pytest.mark.django_db
    def test_targeted_market_serialization(self, targeted_market):
        """Test targeted market serialization."""
        serializer = TargetedMarketSerializer(targeted_market)
        data = serializer.data

        assert data['id'] == str(targeted_market.id)
        assert data['startup'] == str(targeted_market.startup.id)
        assert data['market_name'] == targeted_market.market_name
        assert data['description'] == targeted_market.description

        assert data['market_size'] == f"{targeted_market.market_size:.2f}"
        assert data['market_share'] == f"{targeted_market.market_share:.2f}"

    @pytest.mark.django_db
    def test_targeted_market_deserialization(self, startup_profile):
        """Test targeted market deserialization."""
        data = {
            'startup': startup_profile.id,
            'market_name': 'Enterprise',
            'description': 'Large enterprises',
            'market_size': '500.00',
            'market_share': '10.00',
            'market_type': 'gcc',
            'is_primary': False
        }

        serializer = TargetedMarketSerializer(data=data)
        assert serializer.is_valid()
        market = serializer.save()

        assert market.startup == startup_profile
        assert market.market_name == 'Enterprise'
        assert market.description == 'Large enterprises'
        assert market.market_size == 500.00
        assert market.market_share == 10.00

    @pytest.mark.django_db
    def test_targeted_market_validation_errors(self):
        """Test targeted market validation errors."""
        data = {
            'startup': 'invalid-uuid',
            'market_name': '',
            'market_size': 'invalid',
            'market_share': 'invalid'
        }

        serializer = TargetedMarketSerializer(data=data)
        assert not serializer.is_valid()
        

        assert len(serializer.errors) > 0
        

        print(f"Validation errors: {serializer.errors}")
        
        # Check that at least one field has validation errors
        assert len(serializer.errors) >= 1


class TestCompanyMemberSerializer:
    """Test cases for CompanyMemberSerializer."""

    @pytest.mark.django_db
    def test_company_member_serialization(self, company_member):
        """Test company member serialization."""
        serializer = CompanyMemberSerializer(company_member)
        data = serializer.data


        assert data['id'] == str(company_member.id)
        assert data['startup'] == company_member.startup.id
        assert data['user'] == company_member.user.id
        assert data['member_type'] == company_member.member_type
        assert data['position'] == company_member.position
        assert data['is_current'] == company_member.is_current
        assert data['is_primary_contact'] == company_member.is_primary_contact

    @pytest.mark.django_db
    def test_company_member_deserialization(self, startup_profile, user):
        """Test company member deserialization."""
        data = {
            'startup': startup_profile.id,
            'user': user.id,
            'member_type': 'employee',
            'position': 'Developer',
            'is_current': True,
            'is_primary_contact': False
        }

        serializer = CompanyMemberSerializer(data=data)
        assert serializer.is_valid()
        member = serializer.save()

        assert member.startup == startup_profile
        assert member.user == user
        assert member.member_type == 'employee'
        assert member.position == 'Developer'
        assert member.is_current is True
        assert member.is_primary_contact is False

    def test_company_member_validation_errors(self):
        """Test company member validation errors."""
        data = {
            'startup': 'invalid-uuid',  # Invalid UUID
            'user': 'invalid-uuid',  # Invalid UUID
            'member_type': 'invalid_type',  # Invalid choice
            'position': '',  # Empty position
        }

        serializer = CompanyMemberSerializer(data=data)
        assert not serializer.is_valid()
        assert 'startup' in serializer.errors
        assert 'user' in serializer.errors
        assert 'member_type' in serializer.errors
        assert 'position' in serializer.errors

    @pytest.mark.django_db
    def test_company_member_member_type_choices(self, startup_profile, user):
        """Test valid member type choices."""
        valid_types = ['founder', 'co_founder', 'employee', 'advisor', 'consultant', 'intern', 'contractor']
        
        for member_type in valid_types:
            data = {
                'startup': startup_profile.id,
                'user': user.id,
                'member_type': member_type,
                'position': 'Test Position'
            }

            serializer = CompanyMemberSerializer(data=data)
            assert serializer.is_valid(), f"Member type '{member_type}' should be valid"
