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


class SalesmanUserFactory(BaseUserFactory):
    """Factory for creating salesman users."""

    role = "salesman"
    email = factory.Sequence(lambda n: f"salesman{n}_{uuid.uuid4().hex[:8]}@test.com")
    username = factory.Sequence(lambda n: f"salesman{n}_{uuid.uuid4().hex[:8]}")
    fullname = factory.Sequence(lambda n: f"Salesman {n}")


class CardCreatorUserFactory(BaseUserFactory):
    """Factory for creating card creator users."""

    role = "card_creator"
    email = factory.Sequence(
        lambda n: f"cardcreator{n}_{uuid.uuid4().hex[:8]}@test.com"
    )
    username = factory.Sequence(lambda n: f"cardcreator{n}_{uuid.uuid4().hex[:8]}")
    fullname = factory.Sequence(lambda n: f"Card Creator {n}")


class IssuerUserFactory(BaseUserFactory):
    """Factory for creating issuer users."""

    role = "issuer"
    email = factory.Sequence(lambda n: f"issuer{n}_{uuid.uuid4().hex[:8]}@test.com")
    username = factory.Sequence(lambda n: f"issuer{n}_{uuid.uuid4().hex[:8]}")
    fullname = factory.Sequence(lambda n: f"Issuer {n}")
    is_active = True
    is_email_verified = True


class InfluencerUserFactory(BaseUserFactory):
    """Factory for creating influencer users."""

    role = "influencer"
    email = factory.Sequence(lambda n: f"influencer{n}_{uuid.uuid4().hex[:8]}@test.com")
    username = factory.Sequence(lambda n: f"influencer{n}_{uuid.uuid4().hex[:8]}")
    fullname = factory.Sequence(lambda n: f"Influencer {n}")
    is_verified = True
