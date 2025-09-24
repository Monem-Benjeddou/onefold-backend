"""
Comprehensive test file demonstrating all user factory types.

This file shows how to use all the different user factories for testing
various user types and scenarios.
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from .factories import (
    
    UserFactory,
    AdminUserFactory,
    ModeratorUserFactory,
    CoachUserFactory,
    SuperUserFactory,
    ServiceUserFactory,
    SalesmanUserFactory,
    CardCreatorUserFactory,
    IssuerUserFactory,
    InfluencerUserFactory,
    
    
    FounderUserFactory,
    ReviewerUserFactory,
    EmployeeUserFactory,
    
    
    ManufacturerUserFactory,
    CollectorUserFactory,
    DoctorUserFactory,
    
    
    BannedUserFactory,
    DeactivatedUserFactory,
    UnverifiedUserFactory,
    VerifiedUserFactory,
    UserWithPhoneFactory,
    UserWithCountryFactory,
    UserWithProfileFactory,
    
    
    AnyUserFactory,
    
    
    create_admin_user,
    create_founder_user,
    create_reviewer_user,
    create_regular_user,
    create_banned_user,
    create_superuser,
)

User = get_user_model()


class TestUserFactories(TestCase):
    """Test all user factory types."""

    def test_basic_user_factory(self):
        """Test basic user factory."""
        user = UserFactory()
        self.assertEqual(user.role, "user")
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_email_verified)
        self.assertFalse(user.is_verified)

    def test_admin_user_factory(self):
        """Test admin user factory."""
        user = AdminUserFactory()
        self.assertEqual(user.role, "admin")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_active)

    def test_founder_user_factory(self):
        """Test founder user factory."""
        user = FounderUserFactory()
        self.assertEqual(user.role, "founder")
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_email_verified)

    def test_reviewer_user_factory(self):
        """Test reviewer user factory."""
        user = ReviewerUserFactory()
        self.assertEqual(user.role, "reviewer")
        self.assertTrue(user.is_active)

    def test_employee_user_factory(self):
        """Test employee user factory."""
        user = EmployeeUserFactory()
        self.assertEqual(user.role, "employee")
        self.assertTrue(user.is_active)

    def test_banned_user_factory(self):
        """Test banned user factory."""
        user = BannedUserFactory()
        self.assertTrue(user.is_banned)
        self.assertIsNotNone(user.ban_reason)
        self.assertIsNotNone(user.banned_at)
        self.assertIsNotNone(user.ban_expires_at)

    def test_deactivated_user_factory(self):
        """Test deactivated user factory."""
        user = DeactivatedUserFactory()
        self.assertTrue(user.is_deactivated)
        self.assertIsNotNone(user.deactivated_at)
        self.assertIsNotNone(user.deactivation_reason)

    def test_unverified_user_factory(self):
        """Test unverified user factory."""
        user = UnverifiedUserFactory()
        self.assertFalse(user.is_email_verified)
        self.assertFalse(user.is_verified)

    def test_verified_user_factory(self):
        """Test verified user factory."""
        user = VerifiedUserFactory()
        self.assertTrue(user.is_email_verified)
        self.assertTrue(user.is_verified)

    def test_user_with_phone_factory(self):
        """Test user with phone factory."""
        user = UserWithPhoneFactory()
        self.assertIsNotNone(user.phone_number)
        self.assertTrue(user.is_phone_verified)

    def test_user_with_country_factory(self):
        """Test user with country factory."""
        user = UserWithCountryFactory()
        self.assertIsNotNone(user.country)
        self.assertEqual(user.country.name, "Test Country")

    def test_user_with_profile_factory(self):
        """Test user with complete profile factory."""
        user = UserWithProfileFactory()
        self.assertIsNotNone(user.fullname)
        self.assertIsNotNone(user.date_of_birth)
        self.assertIsNotNone(user.gender)
        self.assertIsNotNone(user.phone_number)
        self.assertTrue(user.is_phone_verified)
        self.assertTrue(user.is_email_verified)
        self.assertTrue(user.is_verified)
        self.assertIsNotNone(user.country)

    def test_any_user_factory_basic(self):
        """Test AnyUserFactory with basic usage."""
        user = AnyUserFactory()
        self.assertEqual(user.role, "user")
        self.assertTrue(user.is_active)

    def test_any_user_factory_with_role(self):
        """Test AnyUserFactory with specific role."""
        user = AnyUserFactory(role="founder")
        self.assertEqual(user.role, "founder")

    def test_any_user_factory_with_custom_attributes(self):
        """Test AnyUserFactory with custom attributes."""
        user = AnyUserFactory(
            role="admin",
            is_staff=True,
            is_banned=True,
            ban_reason="Test ban"
        )
        self.assertEqual(user.role, "admin")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_banned)
        self.assertEqual(user.ban_reason, "Test ban")

    def test_any_user_factory_with_groups(self):
        """Test AnyUserFactory with groups."""
        user = AnyUserFactory(groups=["Admin", "Moderator"])
        self.assertEqual(user.groups.count(), 2)
        group_names = [group.name for group in user.groups.all()]
        self.assertIn("Admin", group_names)
        self.assertIn("Moderator", group_names)

    def test_convenience_functions(self):
        """Test convenience functions."""
        
        admin = create_admin_user()
        self.assertEqual(admin.role, "admin")
        self.assertTrue(admin.is_staff)

        
        founder = create_founder_user()
        self.assertEqual(founder.role, "founder")

        
        reviewer = create_reviewer_user()
        self.assertEqual(reviewer.role, "reviewer")

        
        regular = create_regular_user()
        self.assertEqual(regular.role, "user")

        
        banned = create_banned_user()
        self.assertTrue(banned.is_banned)

        
        superuser = create_superuser()
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)

    def test_all_role_types(self):
        """Test all available role types."""
        roles = [
            "user", "admin", "moderator", "service", "founder", "reviewer",
            "employee", "influencer", "manufacturer", "collector", "issuer",
            "salesman", "card_creator", "coach", "doctor"
        ]
        
        for role in roles:
            user = AnyUserFactory(role=role)
            self.assertEqual(user.role, role)
            self.assertTrue(user.is_active)

    def test_factory_with_custom_email(self):
        """Test factory with custom email."""
        custom_email = "custom@example.com"
        user = AnyUserFactory(email=custom_email)
        self.assertEqual(user.email, custom_email)

    def test_factory_with_custom_username(self):
        """Test factory with custom username."""
        custom_username = "custom_username"
        user = AnyUserFactory(username=custom_username)
        self.assertEqual(user.username, custom_username)

    def test_factory_with_custom_password(self):
        """Test factory with custom password."""
        custom_password = "custom_password_123"
        user = AnyUserFactory(password=custom_password)
        self.assertTrue(user.check_password(custom_password))

    def test_factory_batch_creation(self):
        """Test creating multiple users at once."""
        users = AnyUserFactory.create_batch(5, role="founder")
        self.assertEqual(len(users), 5)
        for user in users:
            self.assertEqual(user.role, "founder")

    def test_factory_with_mixed_attributes(self):
        """Test factory with mixed attributes."""
        user = AnyUserFactory(
            role="founder",
            is_verified=True,
            is_banned=False,
            phone_number="+1234567890",
            is_phone_verified=True,
            gender="male",
            groups=["Founder", "Admin"]
        )
        
        self.assertEqual(user.role, "founder")
        self.assertTrue(user.is_verified)
        self.assertFalse(user.is_banned)
        self.assertEqual(user.phone_number, "+1234567890")
        self.assertTrue(user.is_phone_verified)
        self.assertEqual(user.gender, "male")
        self.assertEqual(user.groups.count(), 2)


class TestUserFactoryIntegration(TestCase):
    """Test user factory integration with other models."""

    def test_user_factory_with_country_model(self):
        """Test user factory integration with country model."""
        from apps.countries.models import Country
        
        
        country = Country.objects.create(
            name="Test Country",
            iso2="TC",
            iso3="TST",
            numeric="999"
        )
        
        
        user = AnyUserFactory(country=country)
        self.assertEqual(user.country, country)

    def test_user_factory_with_groups(self):
        """Test user factory integration with Django groups."""
        
        admin_group = Group.objects.create(name="Admin")
        moderator_group = Group.objects.create(name="Moderator")
        
        
        user = AnyUserFactory(groups=["Admin", "Moderator"])
        
        self.assertEqual(user.groups.count(), 2)
        self.assertIn(admin_group, user.groups.all())
        self.assertIn(moderator_group, user.groups.all())

    def test_user_factory_username_generation(self):
        """Test that username generation works correctly."""
        user1 = AnyUserFactory(fullname="John Doe")
        user2 = AnyUserFactory(fullname="Jane Smith")
        
        
        self.assertIsNotNone(user1.username)
        self.assertIsNotNone(user2.username)
        self.assertNotEqual(user1.username, user2.username)

    def test_user_factory_email_uniqueness(self):
        """Test that email generation creates unique emails."""
        users = AnyUserFactory.create_batch(10)
        emails = [user.email for user in users]
        
        
        self.assertEqual(len(emails), len(set(emails)))



@pytest.fixture
def admin_user():
    """Pytest fixture for admin user."""
    return create_admin_user()


@pytest.fixture
def founder_user():
    """Pytest fixture for founder user."""
    return create_founder_user()


@pytest.fixture
def reviewer_user():
    """Pytest fixture for reviewer user."""
    return create_reviewer_user()


@pytest.fixture
def regular_user():
    """Pytest fixture for regular user."""
    return create_regular_user()


@pytest.fixture
def banned_user():
    """Pytest fixture for banned user."""
    return create_banned_user()


@pytest.fixture
def superuser():
    """Pytest fixture for superuser."""
    return create_superuser()


@pytest.fixture
def users_by_role():
    """Pytest fixture that creates users of all roles."""
    roles = [
        "user", "admin", "moderator", "service", "founder", "reviewer",
        "employee", "influencer", "manufacturer", "collector", "issuer",
        "salesman", "card_creator", "coach", "doctor"
    ]
    
    return {role: AnyUserFactory(role=role) for role in roles}



def test_example_pytest_usage(admin_user, founder_user):
    """Example of using pytest fixtures."""
    assert admin_user.role == "admin"
    assert founder_user.role == "founder"
    assert admin_user.is_staff
    assert not founder_user.is_staff


def test_example_with_users_by_role(users_by_role):
    """Example of using the users_by_role fixture."""
    assert users_by_role["admin"].role == "admin"
    assert users_by_role["founder"].role == "founder"
    assert users_by_role["reviewer"].role == "reviewer"
