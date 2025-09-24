"""
Pytest configuration and fixtures for company app testing.
"""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.accounts.user.models import User
from apps.accounts.user.tests.factories import (
    AnyUserFactory,
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


@pytest.fixture
def user():
    """Create a test user."""
    return create_founder_user(
        username="testuser",
        email="test@example.com",
        phone_number="+1234567890",
        password="testpassword"
    )


@pytest.fixture
def admin_user():
    """Create an admin user."""
    return create_admin_user(
        username="admin",
        email="admin@example.com",
        phone_number="+1234567891",
        password="adminpassword"
    )


@pytest.fixture
def reviewer_user():
    """Create a reviewer user."""
    return create_reviewer_user(
        username="reviewer",
        email="reviewer@example.com",
        phone_number="+1234567892",
        password="reviewerpassword"
    )


@pytest.fixture
def startup_profile(user):
    """Create a test startup profile."""
    return StartupProfile.objects.create(
        startup_name="Test Startup",
        startup_industry="Technology",
        website_link="https://teststartup.com",
        location="San Francisco, CA",
        founded_year=2020,
        bio="A test startup for testing purposes",
        linkedin_url="https://linkedin.com/company/teststartup",
        twitter_url="https://twitter.com/teststartup",
        is_verified=True,
        is_public=True,
        is_active=True,
        primary_founder=user
    )


@pytest.fixture
def another_startup_profile(admin_user):
    """Create another test startup profile."""
    return StartupProfile.objects.create(
        startup_name="Another Startup",
        startup_industry="Healthcare",
        website_link="https://anotherstartup.com",
        location="New York, NY",
        founded_year=2019,
        bio="Another test startup",
        is_verified=False,
        is_public=True,
        is_active=True,
        primary_founder=admin_user
    )


@pytest.fixture
def startup_service_product(startup_profile):
    """Create a test startup service/product."""
    return StartupServiceProduct.objects.create(
        startup=startup_profile,
        name="AI Analytics Platform",
        description="Advanced analytics solution for businesses",
        is_active=True
    )


@pytest.fixture
def development_stage():
    """Create a test development stage."""
    return DevelopmentStage.objects.create(
        name="MVP",
        description="Minimum Viable Product stage",
        order=1
    )


@pytest.fixture
def startup_development_stage(startup_profile, development_stage):
    """Create a test startup development stage."""
    return StartupDevelopmentStage.objects.create(
        startup=startup_profile,
        stage=development_stage,
        assigned_date="2023-01-01",
        notes="Currently working on MVP"
    )


@pytest.fixture
def targeted_market(startup_profile):
    """Create a test targeted market."""
    return TargetedMarket.objects.create(
        startup=startup_profile,
        market_name="SMEs",
        description="Small and medium enterprises",
        market_size=1000.00,
        market_share=5.00,
        market_type="local",
        is_primary=True
    )


@pytest.fixture
def company_member(startup_profile, user):
    """Create a test company member."""
    return CompanyMember.objects.create(
        startup=startup_profile,
        user=user,
        member_type="founder",
        position="CEO",
        is_current=True,
        is_primary_contact=True
    )


@pytest.fixture
def test_image():
    """Create a test image file."""
    return SimpleUploadedFile(
        "test_logo.png",
        b"fake image content",
        content_type="image/png"
    )


@pytest.fixture
def test_pitch_deck():
    """Create a test pitch deck file."""
    return SimpleUploadedFile(
        "test_pitch.pdf",
        b"fake pdf content",
        content_type="application/pdf"
    )
