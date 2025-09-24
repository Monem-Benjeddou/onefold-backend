"""
Factory fixtures for User and Group testing.

This module provides factory_boy factories for creating test users and assigning
groups explicitly in test setup, following Senior Django Developer best practices
for declarative and repeatable tests.

Author: Senior Django Developer (20+ years experience)
"""

import factory
import uuid
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from apps.accounts.user.models import User

User = get_user_model()


class GroupFactory(factory.django.DjangoModelFactory):
    """Factory for creating test Groups."""

    class Meta:
        model = Group
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"TestGroup{n}")


class BaseUserFactory(factory.django.DjangoModelFactory):
    """Base factory for creating test users without automatic group assignment."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}_{uuid.uuid4().hex[:8]}@test.com")
    username = factory.Sequence(lambda n: f"user{n}_{uuid.uuid4().hex[:8]}")
    fullname = factory.Faker("name")
    role = "user"
    is_active = True
    is_email_verified = True
    is_verified = False

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        """Set password after user creation."""
        if not create:
            return

        password = extracted or "testpass123"
        obj.set_password(password)
        obj.save()


class UserFactory(BaseUserFactory):
    """Standard user factory - creates user without any group assignments."""

    pass


class UserWithGroupFactory(BaseUserFactory):
    """
    Factory for creating users with explicit group assignment.

    Usage:
        user = UserWithGroupFactory(groups=['Admin'])
        user = UserWithGroupFactory(groups=['Moderator', 'Coach'])
    """

    class Meta:
        model = User
        skip_postgeneration_save = True

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        """
        Explicitly assign groups after user creation.

        This follows the principle of explicit group assignment rather than
        automatic assignment based on role field.
        """
        if not create:
            return

        if extracted:
            for group_name in extracted:
                group, created = Group.objects.get_or_create(name=group_name)
                self.groups.add(group)


class AdminUserFactory(BaseUserFactory):
    """Factory for creating admin users with explicit Admin group assignment."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    role = "admin"
    is_staff = True

    @factory.post_generation
    def assign_admin_group(self, create, extracted, **kwargs):
        """Explicitly assign Admin group."""
        if not create:
            return

        admin_group, created = Group.objects.get_or_create(name="Admin")
        self.groups.add(admin_group)


class ModeratorUserFactory(BaseUserFactory):
    """Factory for creating moderator users with explicit Moderator group assignment."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    role = "moderator"

    @factory.post_generation
    def assign_moderator_group(self, create, extracted, **kwargs):
        """Explicitly assign Moderator group."""
        if not create:
            return

        moderator_group, created = Group.objects.get_or_create(name="Moderator")
        self.groups.add(moderator_group)


class CoachUserFactory(BaseUserFactory):
    """Factory for creating coach users with explicit Coach group assignment."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    role = "coach"

    @factory.post_generation
    def assign_coach_group(self, create, extracted, **kwargs):
        """Explicitly assign Coach group."""
        if not create:
            return

        coach_group, created = Group.objects.get_or_create(name="Coach")
        self.groups.add(coach_group)


class SuperUserFactory(BaseUserFactory):
    """Factory for creating superusers."""

    is_superuser = True
    is_staff = True
    role = "admin"


class ServiceUserFactory(BaseUserFactory):
    """Factory for creating service account users with explicit Service group assignment."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    role = "service"
    email = factory.Sequence(lambda n: f"service{n}@api.test")
    username = factory.Sequence(lambda n: f"service{n}")
    fullname = factory.Sequence(lambda n: f"Service Account {n}")

    @factory.post_generation
    def assign_service_group(self, create, extracted, **kwargs):
        """Explicitly assign Service group."""
        if not create:
            return

        service_group, created = Group.objects.get_or_create(name="Service")
        self.groups.add(service_group)





class FounderUserFactory(BaseUserFactory):
    """Factory for creating founder users (company-specific role)."""

    role = "founder"
    email = factory.Sequence(lambda n: f"founder{n}_{uuid.uuid4().hex[:8]}@test.com")
    username = factory.Sequence(lambda n: f"founder{n}_{uuid.uuid4().hex[:8]}")
    fullname = factory.Sequence(lambda n: f"Founder {n}")


class ReviewerUserFactory(BaseUserFactory):
    """Factory for creating reviewer users (company-specific role)."""

    role = "reviewer"
    email = factory.Sequence(lambda n: f"reviewer{n}_{uuid.uuid4().hex[:8]}@test.com")
    username = factory.Sequence(lambda n: f"reviewer{n}_{uuid.uuid4().hex[:8]}")
    fullname = factory.Sequence(lambda n: f"Reviewer {n}")


class EmployeeUserFactory(BaseUserFactory):
    """Factory for creating employee users (company-specific role)."""

    role = "employee"
    email = factory.Sequence(lambda n: f"employee{n}_{uuid.uuid4().hex[:8]}@test.com")
    username = factory.Sequence(lambda n: f"employee{n}_{uuid.uuid4().hex[:8]}")
    fullname = factory.Sequence(lambda n: f"Employee {n}")


class ManufacturerUserFactory(BaseUserFactory):
    """Factory for creating manufacturer users."""

    role = "manufacturer"
    email = factory.Sequence(lambda n: f"manufacturer{n}_{uuid.uuid4().hex[:8]}@test.com")
    username = factory.Sequence(lambda n: f"manufacturer{n}_{uuid.uuid4().hex[:8]}")
    fullname = factory.Sequence(lambda n: f"Manufacturer {n}")


class CollectorUserFactory(BaseUserFactory):
    """Factory for creating collector users."""

    role = "collector"
    email = factory.Sequence(lambda n: f"collector{n}_{uuid.uuid4().hex[:8]}@test.com")
    username = factory.Sequence(lambda n: f"collector{n}_{uuid.uuid4().hex[:8]}")
    fullname = factory.Sequence(lambda n: f"Collector {n}")


class DoctorUserFactory(BaseUserFactory):
    """Factory for creating doctor users (legacy role)."""

    role = "doctor"
    email = factory.Sequence(lambda n: f"doctor{n}_{uuid.uuid4().hex[:8]}@test.com")
    username = factory.Sequence(lambda n: f"doctor{n}_{uuid.uuid4().hex[:8]}")
    fullname = factory.Sequence(lambda n: f"Dr. {n}")


class BannedUserFactory(BaseUserFactory):
    """Factory for creating banned users."""

    is_banned = True
    ban_reason = factory.Faker("sentence", nb_words=6)
    banned_at = factory.LazyFunction(timezone.now)
    ban_expires_at = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=30))


class DeactivatedUserFactory(BaseUserFactory):
    """Factory for creating deactivated users."""

    is_deactivated = True
    deactivated_at = factory.LazyFunction(timezone.now)
    deactivation_reason = factory.Faker("sentence", nb_words=6)


class UnverifiedUserFactory(BaseUserFactory):
    """Factory for creating unverified users."""

    is_email_verified = False
    is_verified = False


class VerifiedUserFactory(BaseUserFactory):
    """Factory for creating verified users."""

    is_email_verified = True
    is_verified = True


class UserWithPhoneFactory(BaseUserFactory):
    """Factory for creating users with phone numbers."""

    phone_number = factory.Faker("phone_number")
    is_phone_verified = True


class UserWithCountryFactory(BaseUserFactory):
    """Factory for creating users with country information."""

    @factory.post_generation
    def country(obj, create, extracted, **kwargs):
        """Set country after user creation."""
        if not create:
            return
        
        if extracted:
            obj.country = extracted
            obj.save()
        else:
            # Create a test country if none provided
            from apps.countries.models import Country
            country, created = Country.objects.get_or_create(
                name="Test Country",
                defaults={
                    "iso2": "TC",
                    "iso3": "TST",
                    "numeric": "999"
                }
            )
            obj.country = country
            obj.save()


class UserWithProfileFactory(BaseUserFactory):
    """Factory for creating users with complete profile information."""

    fullname = factory.Faker("name")
    date_of_birth = factory.Faker("date_of_birth", minimum_age=18, maximum_age=80)
    gender = factory.Iterator(["male", "female"])
    phone_number = factory.Faker("phone_number")
    is_phone_verified = True
    is_email_verified = True
    is_verified = True

    @factory.post_generation
    def country(obj, create, extracted, **kwargs):
        """Set country after user creation."""
        if not create:
            return
        
        if extracted:
            obj.country = extracted
            obj.save()
        else:
            # Create a test country if none provided
            from apps.countries.models import Country
            country, created = Country.objects.get_or_create(
                name="Test Country",
                defaults={
                    "iso2": "TC",
                    "iso3": "TST",
                    "numeric": "999"
                }
            )
            obj.country = country
            obj.save()


# Comprehensive factory that can create any user type
class AnyUserFactory(BaseUserFactory):
    """
    Comprehensive factory that can create users of any type.
    
    Usage:
        # Create specific role users
        admin_user = AnyUserFactory(role="admin")
        founder_user = AnyUserFactory(role="founder")
        
        # Create users with specific attributes
        banned_user = AnyUserFactory(is_banned=True, ban_reason="Test ban")
        verified_user = AnyUserFactory(is_verified=True, is_email_verified=True)
        
        # Create users with groups
        user_with_groups = AnyUserFactory(groups=["Admin", "Moderator"])
    """

    class Meta:
        model = User
        skip_postgeneration_save = True

    # Default to regular user
    role = "user"
    
    # Allow customization of all user fields
    email = factory.Sequence(lambda n: f"user{n}_{uuid.uuid4().hex[:8]}@test.com")
    username = factory.Sequence(lambda n: f"user{n}_{uuid.uuid4().hex[:8]}")
    fullname = factory.Faker("name")
    is_active = True
    is_staff = False
    is_superuser = False
    is_email_verified = True
    is_verified = False
    is_banned = False
    is_deactivated = False
    phone_number = None
    is_phone_verified = False
    date_of_birth = None
    gender = None
    ban_reason = None
    banned_at = None
    ban_expires_at = None
    banned_by = None
    deactivated_at = None
    deactivation_reason = None

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        """Set password after user creation."""
        if not create:
            return

        password = extracted or "testpass123"
        obj.set_password(password)
        obj.save()

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        """
        Explicitly assign groups after user creation.
        
        Usage:
            user = AnyUserFactory(groups=['Admin', 'Moderator'])
        """
        if not create:
            return

        if extracted:
            for group_name in extracted:
                group, created = Group.objects.get_or_create(name=group_name)
                self.groups.add(group)

    @factory.post_generation
    def country(obj, create, extracted, **kwargs):
        """Set country after user creation."""
        if not create:
            return
        
        if extracted:
            obj.country = extracted
            obj.save()
        # Don't auto-create country if none provided - let tests be explicit


# Convenience functions for common user types
def create_admin_user(**kwargs):
    """Create an admin user with default admin settings."""
    return AnyUserFactory(
        role="admin",
        is_staff=True,
        is_email_verified=True,
        **kwargs
    )


def create_founder_user(**kwargs):
    """Create a founder user."""
    return AnyUserFactory(
        role="founder",
        is_email_verified=True,
        **kwargs
    )


def create_reviewer_user(**kwargs):
    """Create a reviewer user."""
    return AnyUserFactory(
        role="reviewer",
        is_email_verified=True,
        **kwargs
    )


def create_regular_user(**kwargs):
    """Create a regular user."""
    return AnyUserFactory(
        role="user",
        is_email_verified=True,
        **kwargs
    )


def create_banned_user(**kwargs):
    """Create a banned user."""
    return AnyUserFactory(
        is_banned=True,
        ban_reason=kwargs.get("ban_reason", "Test ban"),
        banned_at=timezone.now(),
        **kwargs
    )


def create_regular_user(**kwargs):
    """Create a regular user."""
    return AnyUserFactory(
        role="user",
        is_email_verified=True,
        **kwargs
    )


def create_superuser(**kwargs):
    """Create a superuser."""
    return AnyUserFactory(
        role="admin",
        is_superuser=True,
        is_staff=True,
        is_email_verified=True,
        **kwargs
    )
