"""
User to Group Assignment Management Command

This command provides explicit, maintainable assignment of users to groups,
following Senior Django Developer best practices for avoiding hidden logic.

Usage:
    python manage.py assign_user_to_group john@example.com Admin
    python manage.py assign_user_to_group jane@example.com Moderator

Author: Senior Django Developer (20+ years experience)
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group
from django.db import transaction
from apps.accounts.user.models import User


class Command(BaseCommand):
    """
    Simple management command for explicit user-to-group assignment.

    This command follows the principle of explicit over implicit assignment,
    ensuring all group memberships are deliberately assigned by operators
    rather than through hidden application logic.
    """

    help = "Assign a user to a group explicitly"

    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            "username_or_email",
            type=str,
            nargs="?",
            help="Username or email of the user to assign",
        )
        parser.add_argument(
            "group_name",
            type=str,
            nargs="?",
            help="Name of the group to assign user to",
        )
        parser.add_argument(
            "--remove",
            action="store_true",
            help="Remove user from group instead of adding",
        )
        parser.add_argument(
            "--list-groups", action="store_true", help="List all available groups"
        )

    def handle(self, *args, **options):
        """Main command handler."""
        try:
            if options["list_groups"]:
                self.list_available_groups()
                return

            username_or_email = options["username_or_email"]
            group_name = options["group_name"]

            if not username_or_email or not group_name:
                raise CommandError(
                    "Both username_or_email and group_name are required. "
                    "Use --list-groups to see available groups."
                )

            remove = options["remove"]

            if remove:
                self.remove_user_from_group(username_or_email, group_name)
            else:
                self.assign_user_to_group(username_or_email, group_name)

        except Exception as e:
            raise CommandError(f"Command failed: {e}")

    def assign_user_to_group(self, username_or_email, group_name):
        """
        Assign user to group with explicit validation and clear error messages.

        Args:
            username_or_email: User identifier (username or email)
            group_name: Name of the group to assign
        """

        user = self.get_user(username_or_email)

        group = self.get_group(group_name)

        if user.groups.filter(name=group_name).exists():
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  User '{user.email}' is already in group '{group_name}'"
                )
            )
            return

        with transaction.atomic():
            user.groups.add(group)

            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Successfully assigned user '{user.email}' to group '{group_name}'"
                )
            )

            current_groups = [g.name for g in user.groups.all()]
            self.stdout.write(f"Current groups: {', '.join(current_groups)}")

    def remove_user_from_group(self, username_or_email, group_name):
        """
        Remove user from group with explicit validation.

        Args:
            username_or_email: User identifier (username or email)
            group_name: Name of the group to remove from
        """

        user = self.get_user(username_or_email)

        group = self.get_group(group_name)

        if not user.groups.filter(name=group_name).exists():
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  User '{user.email}' is not in group '{group_name}'"
                )
            )
            return

        with transaction.atomic():
            user.groups.remove(group)

            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Successfully removed user '{user.email}' from group '{group_name}'"
                )
            )

            current_groups = [g.name for g in user.groups.all()]
            self.stdout.write(
                f"Current groups: {', '.join(current_groups) if current_groups else 'None'}"
            )

    def get_user(self, username_or_email):
        """
        Get user by username or email with clear error message.

        Args:
            username_or_email: User identifier

        Returns:
            User: User instance

        Raises:
            CommandError: If user not found
        """
        try:

            if "@" in username_or_email:
                return User.objects.get(email=username_or_email)
            else:
                return User.objects.get(username=username_or_email)
        except User.DoesNotExist:

            raise CommandError(
                f"❌ User not found: '{username_or_email}'\n"
                f"   Searched by: {'email' if '@' in username_or_email else 'username'}\n"
                f"   Available users: {self.get_available_users_sample()}"
            )

    def get_group(self, group_name):
        """
        Get group by name with clear error message.

        Args:
            group_name: Name of the group

        Returns:
            Group: Group instance

        Raises:
            CommandError: If group not found
        """
        try:
            return Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            available_groups = [g.name for g in Group.objects.all()]
            raise CommandError(
                f"❌ Group not found: '{group_name}'\n"
                f"   Available groups: {', '.join(available_groups) if available_groups else 'None'}\n"
                f"   Use --list-groups to see all available groups"
            )

    def get_available_users_sample(self):
        """Get sample of available users for error messages."""
        users = User.objects.all()[:3]
        return ", ".join([u.email for u in users]) + (
            "..." if users.count() > 3 else ""
        )

    def list_available_groups(self):
        """List all available groups for reference."""
        self.stdout.write(self.style.SUCCESS("📋 Available Groups"))
        self.stdout.write("=" * 40)

        groups = Group.objects.all().order_by("name")
        if not groups.exists():
            self.stdout.write(
                self.style.WARNING("No groups found. Create groups first.")
            )
            return

        for group in groups:
            user_count = group.user_set.count()
            permission_count = group.permissions.count()

            self.stdout.write(
                f"🏷️  {group.name}\n"
                f"   Users: {user_count}\n"
                f"   Permissions: {permission_count}\n"
            )

        self.stdout.write("\nUsage examples:")
        self.stdout.write(
            "  python manage.py assign_user_to_group john@example.com Admin"
        )
        self.stdout.write(
            "  python manage.py assign_user_to_group jane@example.com Moderator"
        )
        self.stdout.write(
            "  python manage.py assign_user_to_group user@example.com Admin --remove"
        )
