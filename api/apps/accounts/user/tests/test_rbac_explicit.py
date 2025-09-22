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

            try:

                forum_ct, _ = ContentType.objects.get_or_create(
                    app_label="apps_forum", model="topic", defaults={"name": "Topic"}
                )

                delete_topic_perm, _ = Permission.objects.get_or_create(
                    codename="delete_topic",
                    content_type=forum_ct,
                    defaults={"name": "Can delete topic"},
                )
                admin_group.permissions.add(delete_topic_perm)

                forum_forum_ct, _ = ContentType.objects.get_or_create(
                    app_label="apps_forum", model="forum", defaults={"name": "Forum"}
                )

                delete_forum_perm, _ = Permission.objects.get_or_create(
                    codename="delete_forum",
                    content_type=forum_forum_ct,
                    defaults={"name": "Can delete forum"},
                )
                admin_group.permissions.add(delete_forum_perm)

                delete_user_perm, _ = Permission.objects.get_or_create(
                    codename="delete_user",
                    content_type=user_ct,
                    defaults={"name": "Can delete user"},
                )
                admin_group.permissions.add(delete_user_perm)
            except:
                pass

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

    def test_multi_group_assignment_via_factory(self):
        """Test assigning multiple groups explicitly via factory."""

        user = UserWithGroupFactory(groups=["Admin", "Moderator"])

        self.assertTrue(user.groups.filter(name="Admin").exists())
        self.assertTrue(user.groups.filter(name="Moderator").exists())
        self.assertEqual(user.groups.count(), 2)

    def test_management_command_assign_user_to_group(self):
        """Test explicit group assignment via management command."""

        user = UserFactory(email="test@example.com")
        self.assertEqual(user.groups.count(), 0)

        call_command("assign_user_to_group", "test@example.com", "Admin")

        user.refresh_from_db()
        self.assertTrue(user.groups.filter(name="Admin").exists())
        self.assertEqual(user.groups.count(), 1)

    def test_management_command_remove_user_from_group(self):
        """Test explicit group removal via management command."""

        user = AdminUserFactory(email="admin@example.com")
        self.assertTrue(user.groups.filter(name="Admin").exists())

        call_command("assign_user_to_group", "admin@example.com", "Admin", "--remove")

        user.refresh_from_db()
        self.assertFalse(user.groups.filter(name="Admin").exists())
        self.assertEqual(user.groups.count(), 0)

    def test_management_command_error_handling(self):
        """Test management command error handling with clear messages."""

        with self.assertRaises(CommandError) as cm:
            call_command("assign_user_to_group", "nonexistent@example.com", "Admin")

        self.assertIn("User not found", str(cm.exception))
        self.assertIn("nonexistent@example.com", str(cm.exception))

        user = UserFactory(email="test@example.com")
        with self.assertRaises(CommandError) as cm:
            call_command("assign_user_to_group", "test@example.com", "NonExistentGroup")

        self.assertIn("Group not found", str(cm.exception))
        self.assertIn("NonExistentGroup", str(cm.exception))

    def test_management_command_duplicate_assignment_warning(self):
        """Test warning when assigning user to group they're already in."""

        user = AdminUserFactory(email="admin@example.com")

        out = StringIO()
        call_command("assign_user_to_group", "admin@example.com", "Admin", stdout=out)

        output = out.getvalue()
        self.assertIn("already in group", output)

    def test_management_command_list_groups(self):
        """Test listing available groups via management command."""
        out = StringIO()
        call_command("assign_user_to_group", "--list-groups", stdout=out)

        output = out.getvalue()
        self.assertIn("Available Groups", output)
        self.assertIn("Admin", output)
        self.assertIn("Moderator", output)

    def test_permission_checking_with_explicit_groups(self):
        """Test that permissions work correctly with explicitly assigned groups."""

        admin_user = AdminUserFactory()

        self.assertTrue(admin_user.has_perm("_user.change_user"))

        regular_user = UserFactory()

        self.assertFalse(regular_user.has_perm("_user.change_user"))

    def test_role_field_independence_from_groups(self):
        """Test that role field doesn't automatically determine group membership."""

        user = UserFactory(role="admin")

        self.assertEqual(user.groups.count(), 0)
        self.assertFalse(user.has_perm("_user.change_user"))

        admin_group = Group.objects.get(name="Admin")
        user.groups.add(admin_group)

        user.refresh_from_db()

        if hasattr(user, "_perm_cache"):
            delattr(user, "_perm_cache")
        if hasattr(user, "_group_perm_cache"):
            delattr(user, "_group_perm_cache")

        self.assertTrue(user.has_perm("_user.change_user"))

    def test_superuser_permissions_independent_of_groups(self):
        """Test that superusers have all permissions regardless of groups."""

        superuser = SuperUserFactory()
        superuser.groups.clear()

        self.assertTrue(superuser.has_perm("_user.delete_user"))
        self.assertTrue(superuser.has_perm("apps_forum.delete_forum"))
        self.assertEqual(superuser.groups.count(), 0)

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

    @override_settings(DEBUG=True)
    def test_explicit_assignment_with_settings_override(self):
        """Test explicit assignment works with settings overrides for isolation."""

        user = AdminUserFactory()

        self.assertTrue(user.groups.filter(name="Admin").exists())
        self.assertTrue(user.has_perm("_user.change_user"))

    def test_no_hidden_group_assignment_logic(self):
        """Test that there's no hidden group assignment logic anywhere."""

        user = UserFactory(role="admin")

        self.assertEqual(user.groups.count(), 0)

        user.role = "moderator"
        user.save()

        self.assertEqual(user.groups.count(), 0)

    def test_management_command_username_and_email_lookup(self):
        """Test that management command works with both username and email."""

        user = UserFactory(username="testuser", email="test@example.com")

        call_command("assign_user_to_group", "test@example.com", "Admin")
        user.refresh_from_db()
        self.assertTrue(user.groups.filter(name="Admin").exists())

        call_command("assign_user_to_group", "test@example.com", "Admin", "--remove")
        user.refresh_from_db()
        self.assertFalse(user.groups.filter(name="Admin").exists())

        call_command("assign_user_to_group", "testuser", "Moderator")
        user.refresh_from_db()
        self.assertTrue(user.groups.filter(name="Moderator").exists())


class ManagementCommandIntegrationTestCase(TestCase):
    """Integration tests for the assign_user_to_group management command."""

    def setUp(self):
        """Set up test groups."""
        Group.objects.get_or_create(name="Admin")
        Group.objects.get_or_create(name="Moderator")
        Group.objects.get_or_create(name="User")

    def test_complete_workflow_via_command(self):
        """Test complete user-to-group assignment workflow via command."""

        user = UserFactory(email="workflow@example.com")

        self.assertEqual(user.groups.count(), 0)

        out = StringIO()
        call_command(
            "assign_user_to_group", "workflow@example.com", "Admin", stdout=out
        )

        user.refresh_from_db()
        self.assertTrue(user.groups.filter(name="Admin").exists())
        self.assertIn("Successfully assigned", out.getvalue())

        call_command("assign_user_to_group", "workflow@example.com", "Moderator")
        user.refresh_from_db()
        self.assertEqual(user.groups.count(), 2)

        out = StringIO()
        call_command(
            "assign_user_to_group",
            "workflow@example.com",
            "Admin",
            "--remove",
            stdout=out,
        )

        user.refresh_from_db()
        self.assertFalse(user.groups.filter(name="Admin").exists())
        self.assertTrue(user.groups.filter(name="Moderator").exists())
        self.assertEqual(user.groups.count(), 1)
        self.assertIn("Successfully removed", out.getvalue())
