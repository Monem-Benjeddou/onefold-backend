"""
Tests for company app views and API endpoints.
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.accounts.user.models import User
from apps.accounts.user.tests.factories import (
    create_founder_user,
    create_admin_user,
    create_reviewer_user,
)
from apps.company.models import (
    StartupProfile,
    StartupServiceProduct,
    DevelopmentStage,
    StartupDevelopmentStage,
    TargetedMarket,
    CompanyMember
)


class TestStartupProfileViewSet(APITestCase):
    """Test cases for StartupProfileViewSet."""

    def setUp(self):
        """Set up test data."""
        self.user = create_founder_user(
            username="testuser",
            email="test@example.com",
            phone_number="+1234567890",
            password="testpassword",
            is_verified=True
        )

        self.admin_user = create_admin_user(
            username="admin",
            email="admin@example.com",
            phone_number="+1234567891",
            password="adminpassword"
        )

        self.reviewer_user = create_reviewer_user(
            username="reviewer",
            email="reviewer@example.com",
            phone_number="+1234567892",
            password="reviewerpassword"
        )

        self.startup = StartupProfile.objects.create(
            startup_name="Test Startup",
            startup_industry="Technology",
            website_link="https://teststartup.com",
            location="San Francisco, CA",
            founded_year=2020,
            bio="A test startup",
            primary_founder=self.user
        )


        CompanyMember.objects.create(
            startup=self.startup,
            user=self.user,
            member_type="founder",
            position="CEO",
            is_current=True,
            is_primary_contact=True
        )

        self.url_list = reverse("startup-profile-list")
        self.url_detail = reverse("startup-profile-detail", kwargs={"pk": self.startup.id})

    def test_list_startup_profiles_authenticated(self):
        """Test listing startup profiles when authenticated."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url_list)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["startup_name"], "Test Startup")

    def test_list_startup_profiles_unauthenticated(self):
        """Test listing startup profiles when not authenticated."""
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_startup_profile_authenticated(self):
        """Test retrieving a startup profile when authenticated."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url_detail)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["startup_name"], "Test Startup")
        self.assertEqual(response.data["startup_industry"], "Technology")

    def test_retrieve_startup_profile_unauthenticated(self):
        """Test retrieving a startup profile when not authenticated."""
        response = self.client.get(self.url_detail)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_startup_profile_authenticated(self):
        """Test creating a startup profile when authenticated."""
        self.client.force_authenticate(user=self.user)
        data = {
            "startup_name": "New Startup",
            "startup_industry": "Healthcare",
            "website_link": "https://newstartup.com",
            "location": "New York, NY",
            "founded_year": 2023,
            "bio": "A new startup",
            "primary_founder": self.user.id
        }

        response = self.client.post(self.url_list, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["startup_name"], "New Startup")
        self.assertTrue(StartupProfile.objects.filter(startup_name="New Startup").exists())

    def test_create_startup_profile_unauthenticated(self):
        """Test creating a startup profile when not authenticated."""
        data = {
            "startup_name": "New Startup",
            "startup_industry": "Healthcare",
            "location": "New York, NY",
            "founded_year": 2023
        }

        response = self.client.post(self.url_list, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_startup_profile_owner(self):
        """Test updating a startup profile as the owner."""
        self.client.force_authenticate(user=self.user)
        data = {
            "startup_name": "Updated Startup Name",
            "bio": "Updated bio"
        }

        response = self.client.patch(self.url_detail, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["startup_name"], "Updated Startup Name")
        self.assertEqual(response.data["bio"], "Updated bio")

    def test_update_startup_profile_non_owner(self):
        """Test updating a startup profile as non-owner."""
        other_user = create_founder_user()
        self.client.force_authenticate(user=other_user)
        data = {
            "startup_name": "Hacked Name"
        }

        response = self.client.patch(self.url_detail, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_startup_profile_admin(self):
        """Test updating a startup profile as admin."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "startup_name": "Admin Updated Name",
            "is_verified": True
        }

        response = self.client.patch(self.url_detail, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["startup_name"], "Admin Updated Name")
        self.assertEqual(response.data["is_verified"], True)

    def test_delete_startup_profile_owner(self):
        """Test deleting a startup profile as the owner."""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.url_detail)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(StartupProfile.objects.filter(id=self.startup.id).exists())

    def test_delete_startup_profile_non_owner(self):
        """Test deleting a startup profile as non-owner."""
        other_user = create_founder_user()
        self.client.force_authenticate(user=other_user)
        response = self.client.delete(self.url_detail)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(StartupProfile.objects.filter(id=self.startup.id).exists())

    def test_upload_logo(self):
        """Test uploading a logo."""
        self.client.force_authenticate(user=self.user)

        test_image = SimpleUploadedFile(
            "test.png",
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc``\x00\x00\x00\x02\x00\x01"
            b"\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82",
            content_type="image/png",
        )

        data = {"logo": test_image}
        response = self.client.patch(self.url_detail, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["logo"])

    def test_upload_pitch_deck(self):
        """Test uploading a pitch deck."""
        self.client.force_authenticate(user=self.user)
        test_pdf = SimpleUploadedFile(
            "test_pitch.pdf",
            b"fake pdf content",
            content_type="application/pdf"
        )

        data = {"pitch_deck_file": test_pdf}
        response = self.client.patch(self.url_detail, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["pitch_deck_file"])


class TestStartupServiceProductViewSet(APITestCase):
    """Test cases for StartupServiceProductViewSet."""

    def setUp(self):
        """Set up test data."""
        self.user = create_founder_user(
            username="testuser",
            email="test@example.com",
            phone_number="+1234567890",
            password="testpassword",
            is_verified=True
        )

        self.admin_user = create_admin_user(
            username="admin",
            email="admin@example.com",
            phone_number="+1234567891",
            password="adminpassword"
        )

        self.reviewer_user = create_reviewer_user(
            username="reviewer",
            email="reviewer@example.com",
            phone_number="+1234567892",
            password="reviewerpassword"
        )

        self.startup = StartupProfile.objects.create(
            startup_name="Test Startup",
            startup_industry="Technology",
            location="San Francisco, CA",
            founded_year=2020,
            primary_founder=self.user
        )

        self.service = StartupServiceProduct.objects.create(
            startup=self.startup,
            name="AI Analytics Platform",
            description="Advanced analytics solution",
            is_active=True
        )


        CompanyMember.objects.create(
            startup=self.startup,
            user=self.user,
            member_type="founder",
            position="CEO",
            is_current=True,
            is_primary_contact=True
        )

        self.url_list = reverse("startup-service-product-list")
        self.url_detail = reverse("startup-service-product-detail", kwargs={"pk": self.service.id})

    def test_list_services_authenticated(self):
        """Test listing services when authenticated."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url_list)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "AI Analytics Platform")

    def test_list_services_unauthenticated(self):
        """Test listing services when not authenticated."""
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_service_authenticated(self):
        """Test retrieving a service when authenticated."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url_detail)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "AI Analytics Platform")
        self.assertEqual(response.data["description"], "Advanced analytics solution")

    def test_create_service_authenticated(self):
        """Test creating a service when authenticated."""
        self.client.force_authenticate(user=self.user)
        data = {
            "startup": self.startup.id,
            "name": "New Service",
            "description": "A new service",
            "is_active": True
        }

        response = self.client.post(self.url_list, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New Service")
        self.assertTrue(StartupServiceProduct.objects.filter(name="New Service").exists())

    def test_create_service_unauthenticated(self):
        """Test creating a service when not authenticated."""
        data = {
            "startup": self.startup.id,
            "name": "New Service",
            "description": "A new service"
        }

        response = self.client.post(self.url_list, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_service_without_startup_id(self):
        """Test creating a service without startup ID."""
        self.client.force_authenticate(user=self.user)
        data = {
            "name": "New Service",
            "description": "A new service"
        }

        response = self.client.post(self.url_list, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_service_invalid_startup_id(self):
        """Test creating a service with invalid startup ID."""
        self.client.force_authenticate(user=self.user)
        data = {
            "startup": "invalid-uuid",
            "name": "New Service",
            "description": "A new service"
        }

        response = self.client.post(self.url_list, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_service_owner(self):
        """Test updating a service as the startup owner."""
        self.client.force_authenticate(user=self.user)
        data = {
            "name": "Updated Service Name",
            "description": "Updated description"
        }

        response = self.client.patch(self.url_detail, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Service Name")
        self.assertEqual(response.data["description"], "Updated description")

    def test_update_service_non_owner(self):
        """Test updating a service as non-owner."""
        other_user = create_founder_user()
        self.client.force_authenticate(user=other_user)
        data = {
            "name": "Hacked Service Name"
        }

        response = self.client.patch(self.url_detail, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_service_owner(self):
        """Test deleting a service as the startup owner."""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.url_detail)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(StartupServiceProduct.objects.filter(id=self.service.id).exists())

    def test_delete_service_non_owner(self):
        """Test deleting a service as non-owner."""
        other_user = create_founder_user()
        self.client.force_authenticate(user=other_user)
        response = self.client.delete(self.url_detail)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(StartupServiceProduct.objects.filter(id=self.service.id).exists())

    def test_founder_can_only_see_own_services(self):
        """Test that founders can only see their own startup's services."""

        other_user = create_founder_user()
        other_startup = StartupProfile.objects.create(
            startup_name="Other Startup",
            startup_industry="Healthcare",
            location="New York, NY",
            founded_year=2021,
            primary_founder=other_user
        )
        other_service = StartupServiceProduct.objects.create(
            startup=other_startup,
            name="Other Service",
            description="Another service"
        )


        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url_list)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "AI Analytics Platform")

    def test_admin_can_see_all_services(self):
        """Test that admins can see all services."""

        other_user = create_founder_user()
        other_startup = StartupProfile.objects.create(
            startup_name="Other Startup",
            startup_industry="Healthcare",
            location="New York, NY",
            founded_year=2021,
            primary_founder=other_user
        )
        other_service = StartupServiceProduct.objects.create(
            startup=other_startup,
            name="Other Service",
            description="Another service"
        )


        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url_list)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_reviewer_can_see_all_services_readonly(self):
        """Test that reviewers can see all services in read-only mode."""

        other_user = create_founder_user()
        other_startup = StartupProfile.objects.create(
            startup_name="Other Startup",
            startup_industry="Healthcare",
            location="New York, NY",
            founded_year=2021,
            primary_founder=other_user
        )
        other_service = StartupServiceProduct.objects.create(
            startup=other_startup,
            name="Other Service",
            description="Another service"
        )


        self.client.force_authenticate(user=self.reviewer_user)
        response = self.client.get(self.url_list)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)


        data = {
            "startup": self.startup.id,
            "name": "Reviewer Service",
            "description": "A service by reviewer"
        }
        response = self.client.post(self.url_list, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestDevelopmentStageViewSet(APITestCase):
    """Test cases for DevelopmentStageViewSet."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = create_admin_user(
            username="admin",
            email="admin@example.com",
            phone_number="+1234567891",
            password="adminpassword"
        )

        self.stage = DevelopmentStage.objects.create(
            name="MVP",
            description="Minimum Viable Product",
            order=1
        )

        self.url_list = reverse("development-stage-list")
        self.url_detail = reverse("development-stage-detail", kwargs={"pk": self.stage.id})

    def test_list_stages_authenticated(self):
        """Test listing development stages when authenticated."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url_list)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "MVP")

    def test_list_stages_unauthenticated(self):
        """Test listing development stages when not authenticated."""
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_stage_authenticated(self):
        """Test retrieving a development stage when authenticated."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url_detail)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "MVP")
        self.assertEqual(response.data["description"], "Minimum Viable Product")

    def test_create_stage_authenticated(self):
        """Test creating a development stage when authenticated."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "name": "Beta",
            "description": "Beta testing stage",
            "order": 2
        }

        response = self.client.post(self.url_list, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Beta")
        self.assertTrue(DevelopmentStage.objects.filter(name="Beta").exists())

    def test_update_stage_authenticated(self):
        """Test updating a development stage when authenticated."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "name": "Updated MVP",
            "description": "Updated description"
        }

        response = self.client.patch(self.url_detail, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated MVP")
        self.assertEqual(response.data["description"], "Updated description")

    def test_delete_stage_authenticated(self):
        """Test deleting a development stage when authenticated."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.url_detail)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(DevelopmentStage.objects.filter(id=self.stage.id).exists())


class TestStartupDevelopmentStageViewSet(APITestCase):
    """Test cases for StartupDevelopmentStageViewSet."""

    def setUp(self):
        """Set up test data."""
        self.user = create_founder_user(
            username="testuser",
            email="test@example.com",
            phone_number="+1234567890",
            password="testpassword",
            is_verified=True
        )

        self.startup = StartupProfile.objects.create(
            startup_name="Test Startup",
            startup_industry="Technology",
            location="San Francisco, CA",
            founded_year=2020,
            primary_founder=self.user
        )

        self.stage = DevelopmentStage.objects.create(
            name="MVP",
            description="Minimum Viable Product",
            order=1
        )

        self.startup_stage = StartupDevelopmentStage.objects.create(
            startup=self.startup,
            stage=self.stage,
            assigned_date="2023-01-01",
            notes="Currently working on MVP"
        )


        CompanyMember.objects.create(
            startup=self.startup,
            user=self.user,
            member_type="founder",
            position="CEO",
            is_current=True,
            is_primary_contact=True
        )

        self.url_list = reverse("startup-development-stage-list")
        self.url_detail = reverse("startup-development-stage-detail", kwargs={"pk": self.startup_stage.id})

    def test_list_startup_stages_authenticated(self):
        """Test listing startup development stages when authenticated."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url_list)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["stage_name"], "MVP")

    def test_retrieve_startup_stage_authenticated(self):
        """Test retrieving a startup development stage when authenticated."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url_detail)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["stage_name"], "MVP")
        self.assertEqual(response.data["notes"], "Currently working on MVP")

    def test_create_startup_stage_authenticated(self):
        """Test creating a startup development stage when authenticated."""
        self.client.force_authenticate(user=self.user)

        new_startup = StartupProfile.objects.create(
            startup_name="Another Startup",
            startup_industry="Technology",
            location="San Francisco, CA",
            founded_year=2021,
            primary_founder=self.user,
        )
        data = {
            "startup": new_startup.id,
            "stage": self.stage.id,
            "assigned_date": "2023-06-01",
            "notes": "New notes"
        }

        response = self.client.post(self.url_list, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["notes"], "New notes")

    def test_update_startup_stage_authenticated(self):
        """Test updating a startup development stage when authenticated."""
        self.client.force_authenticate(user=self.user)
        data = {
            "notes": "Updated notes"
        }

        response = self.client.patch(self.url_detail, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["notes"], "Updated notes")

    def test_delete_startup_stage_authenticated(self):
        """Test deleting a startup development stage when authenticated."""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.url_detail)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(StartupDevelopmentStage.objects.filter(id=self.startup_stage.id).exists())


class TestTargetedMarketViewSet(APITestCase):
    """Test cases for TargetedMarketViewSet."""

    def setUp(self):
        """Set up test data."""
        self.user = create_founder_user(
            username="testuser",
            email="test@example.com",
            phone_number="+1234567890",
            password="testpassword",
            is_verified=True
        )

        self.startup = StartupProfile.objects.create(
            startup_name="Test Startup",
            startup_industry="Technology",
            location="San Francisco, CA",
            founded_year=2020,
            primary_founder=self.user
        )

        self.market = TargetedMarket.objects.create(
            startup=self.startup,
            market_name="SMEs",
            description="Small and medium enterprises",
            market_size=1000.00,
            market_share=5.00,
            market_type="local",
            is_primary=True
        )

        self.url_list = reverse("targeted-market-list")
        self.url_detail = reverse("targeted-market-detail", kwargs={"pk": self.market.id})

    def test_list_markets_authenticated(self):
        """Test listing targeted markets when authenticated."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url_list)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["market_name"], "SMEs")

    def test_retrieve_market_authenticated(self):
        """Test retrieving a targeted market when authenticated."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url_detail)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["market_name"], "SMEs")
        self.assertEqual(response.data["description"], "Small and medium enterprises")

    def test_create_market_authenticated(self):
        """Test creating a targeted market when authenticated."""
        self.client.force_authenticate(user=self.user)
        data = {
            "startup": self.startup.id,
            "market_name": "Enterprise",
            "description": "Large enterprises",
            "market_size": "500.00",
            "market_share": "10.00",
            "market_type": "gcc",
            "is_primary": False
        }

        response = self.client.post(self.url_list, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["market_name"], "Enterprise")

    def test_update_market_authenticated(self):
        """Test updating a targeted market when authenticated."""
        self.client.force_authenticate(user=self.user)
        data = {
            "market_name": "Updated SMEs",
            "market_size": "1500.00"
        }

        response = self.client.patch(self.url_detail, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["market_name"], "Updated SMEs")
        self.assertEqual(response.data["market_size"], "1500.00")

    def test_delete_market_authenticated(self):
        """Test deleting a targeted market when authenticated."""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.url_detail)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TargetedMarket.objects.filter(id=self.market.id).exists())


class TestCompanyMemberViewSet(APITestCase):
    """Test cases for CompanyMemberViewSet."""

    def setUp(self):
        """Set up test data."""
        self.user = create_founder_user(
            username="testuser",
            email="test@example.com",
            phone_number="+1234567890",
            password="testpassword",
            is_verified=True
        )

        self.startup = StartupProfile.objects.create(
            startup_name="Test Startup",
            startup_industry="Technology",
            location="San Francisco, CA",
            founded_year=2020,
            primary_founder=self.user
        )

        self.member = CompanyMember.objects.create(
            startup=self.startup,
            user=self.user,
            member_type="founder",
            position="CEO",
            is_current=True,
            is_primary_contact=True
        )

        self.url_list = reverse("company-member-list")
        self.url_detail = reverse("company-member-detail", kwargs={"pk": self.member.id})

    def test_list_members_authenticated(self):
        """Test listing company members when authenticated."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url_list)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["position"], "CEO")

    def test_retrieve_member_authenticated(self):
        """Test retrieving a company member when authenticated."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url_detail)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["position"], "CEO")
        self.assertEqual(response.data["member_type"], "founder")

    def test_create_member_authenticated(self):
        """Test creating a company member when authenticated."""
        new_user = create_founder_user()
        new_user.role = "employee"
        new_user.save()
        
        self.client.force_authenticate(user=self.user)
        data = {
            "startup": self.startup.id,
            "user": new_user.id,
            "member_type": "employee",
            "position": "Developer",
            "is_current": True,
            "is_primary_contact": False
        }

        response = self.client.post(self.url_list, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["position"], "Developer")

    def test_update_member_authenticated(self):
        """Test updating a company member when authenticated."""
        self.client.force_authenticate(user=self.user)
        data = {
            "position": "CTO",
            "member_type": "co_founder"
        }

        response = self.client.patch(self.url_detail, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["position"], "CTO")
        self.assertEqual(response.data["member_type"], "co_founder")

    def test_delete_member_authenticated(self):
        """Test deleting a company member when authenticated."""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.url_detail)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CompanyMember.objects.filter(id=self.member.id).exists())
