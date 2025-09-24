"""
Basic tests to verify the test setup is working correctly.
"""

import pytest
from django.test import TestCase
from apps.accounts.user.models import User
from apps.accounts.user.tests.factories import (
    AnyUserFactory,
    create_founder_user,
    create_admin_user,
    create_reviewer_user,
    create_regular_user,
)
from apps.company.models import StartupProfile


class TestBasicSetup(TestCase):
    """Basic tests to verify test setup."""

    def test_user_creation(self):
        """Test that we can create a user using factory."""
        user = create_founder_user(
            username="testuser",
            email="test@example.com",
            phone_number="+1234567890"
        )
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.phone_number, "+1234567890")
        self.assertEqual(user.role, "founder")
        self.assertTrue(user.is_email_verified)

    def test_startup_profile_creation(self):
        """Test that we can create a startup profile."""
        user = create_founder_user(
            username="testuser",
            email="test@example.com",
            phone_number="+1234567890"
        )
        
        startup = StartupProfile.objects.create(
            startup_name="Test Startup",
            startup_industry="Technology",
            location="San Francisco, CA",
            founded_year=2020,
            primary_founder=user
        )
        
        self.assertEqual(startup.startup_name, "Test Startup")
        self.assertEqual(startup.primary_founder, user)


@pytest.mark.django_db
def test_pytest_user_creation():
    """Test user creation with pytest using factory."""
    user = create_founder_user(
        username="pytestuser",
        email="pytest@example.com",
        phone_number="+1234567891"
    )
    assert user.username == "pytestuser"
    assert user.email == "pytest@example.com"
    assert user.role == "founder"
    assert user.is_email_verified


@pytest.mark.django_db
def test_pytest_startup_creation():
    """Test startup creation with pytest using factory."""
    user = create_founder_user(
        username="pytestuser",
        email="pytest@example.com",
        phone_number="+1234567891"
    )
    
    startup = StartupProfile.objects.create(
        startup_name="Pytest Startup",
        startup_industry="Technology",
        location="San Francisco, CA",
        founded_year=2020,
        primary_founder=user
    )
    
    assert startup.startup_name == "Pytest Startup"
    assert startup.primary_founder == user


@pytest.mark.django_db
def test_any_user_factory_examples():
    """Test various AnyUserFactory usage examples."""

    admin_user = AnyUserFactory(role="admin", is_staff=True)
    founder_user = AnyUserFactory(role="founder")
    reviewer_user = AnyUserFactory(role="reviewer")
    regular_user = AnyUserFactory(role="user")
    
    assert admin_user.role == "admin"
    assert admin_user.is_staff
    assert founder_user.role == "founder"
    assert reviewer_user.role == "reviewer"
    assert regular_user.role == "user"


@pytest.mark.django_db
def test_user_factory_with_custom_attributes():
    """Test user factory with custom attributes."""

    banned_user = AnyUserFactory(
        role="founder",
        is_banned=True,
        ban_reason="Test ban",
        phone_number="+1234567890",
        is_phone_verified=True
    )
    
    assert banned_user.role == "founder"
    assert banned_user.is_banned
    assert banned_user.ban_reason == "Test ban"
    assert banned_user.phone_number == "+1234567890"
    assert banned_user.is_phone_verified


@pytest.mark.django_db
def test_user_factory_batch_creation():
    """Test creating multiple users at once."""

    founders = AnyUserFactory.create_batch(5, role="founder")
    
    assert len(founders) == 5
    for founder in founders:
        assert founder.role == "founder"
        assert founder.is_active


@pytest.mark.django_db
def test_user_factory_with_groups():
    """Test user factory with Django groups."""
    user = AnyUserFactory(
        role="admin",
        groups=["Admin", "Moderator"]
    )
    
    assert user.role == "admin"
    assert user.groups.count() == 2
    group_names = [group.name for group in user.groups.all()]
    assert "Admin" in group_names
    assert "Moderator" in group_names


@pytest.mark.django_db
def test_convenience_functions():
    """Test convenience functions for common user types."""

    admin = create_admin_user()
    founder = create_founder_user()
    reviewer = create_reviewer_user()
    regular = create_regular_user()
    
    assert admin.role == "admin"
    assert admin.is_staff
    assert founder.role == "founder"
    assert reviewer.role == "reviewer"
    assert regular.role == "user"
    

    assert admin.is_email_verified
    assert founder.is_email_verified
    assert reviewer.is_email_verified
    assert regular.is_email_verified

