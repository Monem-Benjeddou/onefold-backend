"""
Tests for company app permissions and access control.
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from apps.company.models import (
    StartupProfile,
    StartupServiceProduct,
    DevelopmentStage,
    StartupDevelopmentStage,
    TargetedMarket,
    CompanyMember
)
from core.permissions import StartupAccessPermission

User = get_user_model()


class TestStartupAccessPermission(TestCase):
    """Test cases for StartupAccessPermission."""

    def setUp(self):
        """Set up test data."""
        self.founder_user = User.objects.create(
            username="founder",
            email="founder@example.com",
            phone_number="+1234567890",
            is_email_verified=True,
            role="founder"
        )
        
        self.admin_user = User.objects.create(
            username="admin",
            email="admin@example.com",
            phone_number="+1234567891",
            is_email_verified=True,
            role="admin",
            is_staff=True
        )
        
        self.reviewer_user = User.objects.create(
            username="reviewer",
            email="reviewer@example.com",
            phone_number="+1234567892",
            is_email_verified=True,
            role="reviewer"
        )
        
        self.other_founder = User.objects.create(
            username="other_founder",
            email="other@example.com",
            phone_number="+1234567893",
            is_email_verified=True,
            role="founder"
        )
        
        self.regular_user = User.objects.create(
            username="regular",
            email="regular@example.com",
            phone_number="+1234567894",
            is_email_verified=True,
            role="user"
        )

        self.startup = StartupProfile.objects.create(
            startup_name="Test Startup",
            startup_industry="Technology",
            location="San Francisco, CA",
            founded_year=2020,
            primary_founder=self.founder_user
        )

        self.other_startup = StartupProfile.objects.create(
            startup_name="Other Startup",
            startup_industry="Healthcare",
            location="New York, NY",
            founded_year=2021,
            primary_founder=self.other_founder
        )

        self.service = StartupServiceProduct.objects.create(
            startup=self.startup,
            name="Test Service",
            description="A test service"
        )

        self.permission = StartupAccessPermission()

    def test_admin_has_permission(self):
        """Test that admin users have permission."""
        request = type('MockRequest', (), {
            'user': self.admin_user,
            'method': 'GET'
        })()
        
        view = type('MockView', (), {})()
        
        has_permission = self.permission.has_permission(request, view)
        self.assertTrue(has_permission)

    def test_staff_has_permission(self):
        """Test that staff users have permission."""
        staff_user = User.objects.create(
            username="staff",
            email="staff@example.com",
            phone_number="+1234567895",
            is_email_verified=True,
            role="user",
            is_staff=True
        )
        
        request = type('MockRequest', (), {
            'user': staff_user,
            'method': 'GET'
        })()
        
        view = type('MockView', (), {})()
        
        has_permission = self.permission.has_permission(request, view)
        self.assertTrue(has_permission)

    def test_founder_has_permission(self):
        """Test that founder users have permission."""
        request = type('MockRequest', (), {
            'user': self.founder_user,
            'method': 'GET'
        })()
        
        view = type('MockView', (), {})()
        
        has_permission = self.permission.has_permission(request, view)
        self.assertTrue(has_permission)

    def test_reviewer_has_permission(self):
        """Test that reviewer users have permission."""
        request = type('MockRequest', (), {
            'user': self.reviewer_user,
            'method': 'GET'
        })()
        
        view = type('MockView', (), {})()
        
        has_permission = self.permission.has_permission(request, view)
        self.assertTrue(has_permission)

    def test_regular_user_no_permission(self):
        """Test that regular users don't have permission."""
        request = type('MockRequest', (), {
            'user': self.regular_user,
            'method': 'GET'
        })()
        
        view = type('MockView', (), {})()
        
        has_permission = self.permission.has_permission(request, view)
        self.assertFalse(has_permission)

    def test_anonymous_user_no_permission(self):
        """Test that anonymous users don't have permission."""
        request = type('MockRequest', (), {
            'user': None,
            'method': 'GET'
        })()
        
        view = type('MockView', (), {})()
        
        has_permission = self.permission.has_permission(request, view)
        self.assertFalse(has_permission)


class TestStartupOwnershipPermissions(APITestCase):
    """Test cases for startup ownership-based permissions."""

    def setUp(self):
        """Set up test data."""
        self.founder_user = User.objects.create(
            username="founder",
            email="founder@example.com",
            phone_number="+1234567890",
            is_email_verified=True,
            role="founder"
        )
        self.founder_user.set_password("testpassword")
        self.founder_user.save()

        self.other_founder = User.objects.create(
            username="other_founder",
            email="other@example.com",
            phone_number="+1234567893",
            is_email_verified=True,
            role="founder"
        )
        self.other_founder.set_password("testpassword")
        self.other_founder.save()

        self.admin_user = User.objects.create(
            username="admin",
            email="admin@example.com",
            phone_number="+1234567891",
            is_email_verified=True,
            role="admin",
            is_staff=True
        )
        self.admin_user.set_password("adminpassword")
        self.admin_user.save()

        self.startup = StartupProfile.objects.create(
            startup_name="Test Startup",
            startup_industry="Technology",
            location="San Francisco, CA",
            founded_year=2020,
            primary_founder=self.founder_user
        )

        self.other_startup = StartupProfile.objects.create(
            startup_name="Other Startup",
            startup_industry="Healthcare",
            location="New York, NY",
            founded_year=2021,
            primary_founder=self.other_founder
        )

        self.service = StartupServiceProduct.objects.create(
            startup=self.startup,
            name="Test Service",
            description="A test service"
        )

        self.other_service = StartupServiceProduct.objects.create(
            startup=self.other_startup,
            name="Other Service",
            description="Another test service"
        )

    def test_founder_can_access_own_startup(self):
        """Test that founders can access their own startup."""
        self.client.force_authenticate(user=self.founder_user)
        

        url = reverse("startup-profile-detail", kwargs={"pk": self.startup.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


        url = reverse("startup-service-product-detail", kwargs={"pk": self.service.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_founder_cannot_access_other_startup(self):
        """Test that founders cannot access other startups."""
        self.client.force_authenticate(user=self.founder_user)
        

        url = reverse("startup-profile-detail", kwargs={"pk": self.other_startup.id})
        response = self.client.patch(url, {"startup_name": "Hacked Name"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


        url = reverse("startup-service-product-detail", kwargs={"pk": self.other_service.id})
        response = self.client.patch(url, {"name": "Hacked Service"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_founder_can_only_see_own_services_in_list(self):
        """Test that founders can only see their own services in list view."""
        self.client.force_authenticate(user=self.founder_user)
        
        url = reverse("startup-service-product-list")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Test Service")

    def test_admin_can_access_all_startups(self):
        """Test that admins can access all startups."""
        self.client.force_authenticate(user=self.admin_user)
        

        url = reverse("startup-profile-detail", kwargs={"pk": self.startup.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = reverse("startup-profile-detail", kwargs={"pk": self.other_startup.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


        url = reverse("startup-service-product-detail", kwargs={"pk": self.service.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = reverse("startup-service-product-detail", kwargs={"pk": self.other_service.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_can_see_all_services_in_list(self):
        """Test that admins can see all services in list view."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse("startup-service-product-list")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_admin_can_modify_any_startup(self):
        """Test that admins can modify any startup."""
        self.client.force_authenticate(user=self.admin_user)
        

        url = reverse("startup-profile-detail", kwargs={"pk": self.other_startup.id})
        response = self.client.patch(url, {"startup_name": "Admin Updated Name"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["startup_name"], "Admin Updated Name")


        url = reverse("startup-service-product-detail", kwargs={"pk": self.other_service.id})
        response = self.client.patch(url, {"name": "Admin Updated Service"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Admin Updated Service")


class TestCompanyMemberPermissions(APITestCase):
    """Test cases for company member permissions."""

    def setUp(self):
        """Set up test data."""
        self.founder_user = User.objects.create(
            username="founder",
            email="founder@example.com",
            phone_number="+1234567890",
            is_email_verified=True,
            role="founder"
        )
        self.founder_user.set_password("testpassword")
        self.founder_user.save()

        self.employee_user = User.objects.create(
            username="employee",
            email="employee@example.com",
            phone_number="+1234567891",
            is_email_verified=True,
            role="employee"
        )
        self.employee_user.set_password("testpassword")
        self.employee_user.save()

        self.startup = StartupProfile.objects.create(
            startup_name="Test Startup",
            startup_industry="Technology",
            location="San Francisco, CA",
            founded_year=2020,
            primary_founder=self.founder_user
        )

        self.member = CompanyMember.objects.create(
            startup=self.startup,
            user=self.employee_user,
            member_type="employee",
            position="Developer",
            is_current=True
        )

    def test_company_member_can_access_own_membership(self):
        """Test that company members can access their own membership."""
        self.client.force_authenticate(user=self.employee_user)
        
        url = reverse("company-member-detail", kwargs={"pk": self.member.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_founder_can_manage_company_members(self):
        """Test that founders can manage company members."""
        self.client.force_authenticate(user=self.founder_user)
        

        new_user = User.objects.create(
            username="newuser",
            email="new@example.com",
            phone_number="+1234567892",
            is_email_verified=True,
            role="employee"
        )
        
        url = reverse("company-member-list")
        data = {
            "startup": self.startup.id,
            "user": new_user.id,
            "member_type": "employee",
            "position": "Designer",
            "is_current": True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


        url = reverse("company-member-detail", kwargs={"pk": self.member.id})
        response = self.client.patch(url, {"position": "Senior Developer"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test deleting a member
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class TestDevelopmentStagePermissions(APITestCase):
    """Test cases for development stage permissions."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create(
            username="admin",
            email="admin@example.com",
            phone_number="+1234567891",
            is_email_verified=True,
            role="admin",
            is_staff=True
        )
        self.admin_user.set_password("adminpassword")
        self.admin_user.save()

        self.founder_user = User.objects.create(
            username="founder",
            email="founder@example.com",
            phone_number="+1234567890",
            is_email_verified=True,
            role="founder"
        )
        self.founder_user.set_password("testpassword")
        self.founder_user.save()

        self.stage = DevelopmentStage.objects.create(
            name="MVP",
            description="Minimum Viable Product",
            order=1
        )

    def test_admin_can_manage_development_stages(self):
        """Test that admins can manage development stages."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Test creating a stage
        url = reverse("development-stage-list")
        data = {
            "name": "Beta",
            "description": "Beta testing stage",
            "order": 2
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Test updating a stage
        url = reverse("development-stage-detail", kwargs={"pk": self.stage.id})
        response = self.client.patch(url, {"name": "Updated MVP"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test deleting a stage
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_founder_cannot_manage_development_stages(self):
        """Test that founders cannot manage development stages."""
        self.client.force_authenticate(user=self.founder_user)
        
        # Test creating a stage
        url = reverse("development-stage-list")
        data = {
            "name": "Beta",
            "description": "Beta testing stage",
            "order": 2
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Test updating a stage
        url = reverse("development-stage-detail", kwargs={"pk": self.stage.id})
        response = self.client.patch(url, {"name": "Updated MVP"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Test deleting a stage
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestTargetedMarketPermissions(APITestCase):
    """Test cases for targeted market permissions."""

    def setUp(self):
        """Set up test data."""
        self.founder_user = User.objects.create(
            username="founder",
            email="founder@example.com",
            phone_number="+1234567890",
            is_email_verified=True,
            role="founder"
        )
        self.founder_user.set_password("testpassword")
        self.founder_user.save()

        self.other_founder = User.objects.create(
            username="other_founder",
            email="other@example.com",
            phone_number="+1234567893",
            is_email_verified=True,
            role="founder"
        )
        self.other_founder.set_password("testpassword")
        self.other_founder.save()

        self.startup = StartupProfile.objects.create(
            startup_name="Test Startup",
            startup_industry="Technology",
            location="San Francisco, CA",
            founded_year=2020,
            primary_founder=self.founder_user
        )

        self.other_startup = StartupProfile.objects.create(
            startup_name="Other Startup",
            startup_industry="Healthcare",
            location="New York, NY",
            founded_year=2021,
            primary_founder=self.other_founder
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

        self.other_market = TargetedMarket.objects.create(
            startup=self.other_startup,
            market_name="Enterprise",
            description="Large enterprises",
            market_size=500.00,
            market_share=10.00,
            market_type="gcc",
            is_primary=False
        )

    def test_founder_can_manage_own_markets(self):
        """Test that founders can manage their own targeted markets."""
        self.client.force_authenticate(user=self.founder_user)
        
        # Test creating a market
        url = reverse("targeted-market-list")
        data = {
            "startup": self.startup.id,
            "market_name": "Startups",
            "description": "Early stage startups",
            "market_size": "2000.00",
            "market_share": "3.00",
            "market_type": "local",
            "is_primary": True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Test updating a market
        url = reverse("targeted-market-detail", kwargs={"pk": self.market.id})
        response = self.client.patch(url, {"market_name": "Updated SMEs"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test deleting a market
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_founder_cannot_manage_other_markets(self):
        """Test that founders cannot manage other startups' markets."""
        self.client.force_authenticate(user=self.founder_user)
        
        # Test updating another startup's market
        url = reverse("targeted-market-detail", kwargs={"pk": self.other_market.id})
        response = self.client.patch(url, {"market_name": "Hacked Market"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Test deleting another startup's market
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_founder_can_only_see_own_markets_in_list(self):
        """Test that founders can only see their own markets in list view."""
        self.client.force_authenticate(user=self.founder_user)
        
        url = reverse("targeted-market-list")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["market_name"], "SMEs")
