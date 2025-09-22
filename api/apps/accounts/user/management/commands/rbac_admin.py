"""
RBAC Administration Management Command

This management command provides comprehensive RBAC administration capabilities
for managing Django Groups-based role assignments and permissions.

Usage:
    python manage.py rbac_admin --list-groups
    python manage.py rbac_admin --assign-role user@example.com admin
    python manage.py rbac_admin --audit-users

Author: Senior Django Developer (20+ years experience)
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, Permission
from django.db import transaction
from apps.accounts.user.models import User
from apps.accounts.user.rbac import RoleManager, get_user_permission_context


class Command(BaseCommand):
    """Django management command for RBAC administration."""

    help = "Administer the Django Groups-based RBAC system"

    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            "--list-groups", action="store_true", help="List all RBAC groups"
        )
        parser.add_argument(
            "--assign-role",
            nargs=2,
            metavar=("EMAIL", "ROLE"),
            help="Assign role to user",
        )
        parser.add_argument(
            "--audit-users", action="store_true", help="Audit all users"
        )
        parser.add_argument(
            "--get-user-context",
            type=str,
            metavar="EMAIL",
            help="Get user permission context",
        )

    def handle(self, *args, **options):
        """Main command handler."""
        try:
            if options["list_groups"]:
                self.list_groups()
            elif options["assign_role"]:
                email, role = options["assign_role"]
                self.assign_role(email, role)
            elif options["audit_users"]:
                self.audit_users()
            elif options["get_user_context"]:
                self.get_user_context(options["get_user_context"])
            else:
                self.print_help()
        except Exception as e:
            raise CommandError(f"Command failed: {e}")

    def list_groups(self):
        """List all RBAC groups."""
        self.stdout.write(self.style.SUCCESS("🔐 RBAC Groups"))
        groups = Group.objects.all().order_by("name")
        for group in groups:
            perm_count = group.permissions.count()
            user_count = group.user_set.count()
            self.stdout.write(
                f"📋 {group.name}: {perm_count} permissions, {user_count} users"
            )

    def assign_role(self, email, role):
        """Assign role to user."""
        if role not in RoleManager.ROLES:
            raise CommandError(f"Invalid role: {role}")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f"User not found: {email}")

        success = RoleManager.assign_user_to_role(user, role)
        if success:
            user.role = role
            user.save()
            self.stdout.write(self.style.SUCCESS(f"✅ Assigned {role} role to {email}"))
        else:
            raise CommandError("Role assignment failed")

    def audit_users(self):
        """Audit all users."""
        self.stdout.write(self.style.SUCCESS("🔍 User Audit"))
        for user in User.objects.all()[:10]:
            groups = [g.name for g in user.groups.all()]
            self.stdout.write(f"👤 {user.email} | Role: {user.role} | Groups: {groups}")

    def get_user_context(self, email):
        """Get user permission context."""
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f"User not found: {email}")

        context = get_user_permission_context(user)
        self.stdout.write(self.style.SUCCESS(f"👤 {user.email}"))
        self.stdout.write(f"Role: {user.role}")
        self.stdout.write(f"Admin: {context['is_admin']}")
        self.stdout.write(f"Permissions: {len(context['permissions'])}")

    def print_help(self):
        """Print help."""
        self.stdout.write("Available commands:")
        self.stdout.write("--list-groups: List all groups")
        self.stdout.write("--assign-role EMAIL ROLE: Assign role")
        self.stdout.write("--audit-users: Audit users")
        self.stdout.write("--get-user-context EMAIL: Get user context")
