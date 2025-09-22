"""
Explicit RBAC Test Suite

This module tests the explicit group assignment approach, ensuring users are
only assigned to groups through deliberate operator actions, not automatic logic.

Tests follow Senior Django Developer practices:
- Use factory_boy fixtures for declarative test setup
- Assert correct group membership explicitly
- Test management commands for group assignment
- Ensure no automatic group assignment occurs

Author: Senior Django Developer (20+ years experience)
"""

from django.test import TestCase, override_settings
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import CommandError
from unittest import mock
from io import StringIO

from apps.accounts.user.models import User
from apps.accounts.user.tests.factories import (
    UserFactory,
    AdminUserFactory,
    ModeratorUserFactory,
    CoachUserFactory,
    ServiceUserFactory,
    UserWithGroupFactory,
    SuperUserFactory,
)


class ExplicitGroupAssignmentTestCase(TestCase):
    """
    Test explicit group assignment principles.

    Ensures that users are never automatically assigned to groups and that
    all group assignments happen through explicit operator actions.
    """

    def setUp(self):
        """Set up test data using factory fixtures."""
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

        admin_group, _ = Group.objects.get_or_create(name="Admin")
        moderator_group, _ = Group.objects.get_or_create(name="Moderator")
        Group.objects.get_or_create(name="User")
        Group.objects.get_or_create(name="Coach")
        Group.objects.get_or_create(name="Service")

        try:

            from apps.accounts.user.models import User

            user_ct = ContentType.objects.get_for_model(User)

            change_user_perm, _ = Permission.objects.get_or_create(
                codename="change_user",
                content_type=user_ct,
                defaults={"name": "Can change user"},
            )

            admin_group.permissions.add(change_user_perm)

            delete_user_perm, _ = Permission.objects.get_or_create(
                codename="delete_user",
                content_type=user_ct,
                defaults={"name": "Can delete user"},
            )
            admin_group.permissions.add(delete_user_perm)

        except Exception:

            pass

    def test_user_creation_no_automatic_group_assignment(self):
        """Test that creating users doesn't automatically assign groups."""

        user = UserFactory()

        self.assertEqual(user.groups.count(), 0)
        self.assertFalse(user.groups.exists())

        user.role = "admin"
        user.save()

        self.assertEqual(user.groups.count(), 0)

    def test_explicit_group_assignment_via_factory(self):
        """Test explicit group assignment using factory fixtures."""

        admin_user = AdminUserFactory()

        self.assertTrue(admin_user.groups.filter(name="Admin").exists())
        self.assertEqual(admin_user.groups.count(), 1)

        moderator_user = ModeratorUserFactory()

        self.assertTrue(moderator_user.groups.filter(name="Moderator").exists())
        self.assertEqual(moderator_user.groups.count(), 1)

    def test_management_command_assign_user_to_group(self):
        """Test explicit group assignment via management command."""

        user = UserFactory(email="test@example.com")
        self.assertEqual(user.groups.count(), 0)

        call_command("assign_user_to_group", "test@example.com", "Admin")

        user.refresh_from_db()
        self.assertTrue(user.groups.filter(name="Admin").exists())
        self.assertEqual(user.groups.count(), 1)

    def test_factory_fixture_declarative_setup(self):
        """Test that factory fixtures create predictable, declarative test setup."""

        users = {
            "admin": AdminUserFactory(),
            "moderator": ModeratorUserFactory(),
            "coach": CoachUserFactory(),
            "service": ServiceUserFactory(),
            "regular": UserFactory(),
        }

        self.assertTrue(users["admin"].groups.filter(name="Admin").exists())
        self.assertTrue(users["moderator"].groups.filter(name="Moderator").exists())
        self.assertTrue(users["coach"].groups.filter(name="Coach").exists())
        self.assertTrue(users["service"].groups.filter(name="Service").exists())
        self.assertEqual(users["regular"].groups.count(), 0)

        self.assertEqual(users["admin"].groups.count(), 1)
        self.assertEqual(users["moderator"].groups.count(), 1)
        self.assertEqual(users["coach"].groups.count(), 1)
        self.assertEqual(users["service"].groups.count(), 1)
