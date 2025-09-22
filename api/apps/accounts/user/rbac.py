"""
Role-Based Access Control (RBAC) Utilities

This module provides utilities for managing Django Groups-based RBAC system,
following Senior Django Developer best practices for explicit group assignment
and avoiding hidden automatic logic.

Key Principle: Users are assigned to groups explicitly via management commands
or admin interface, never automatically through application logic.

Author: Senior Django Developer (20+ years experience)
"""

from typing import List, Optional, Set
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


class GroupManager:
    """
    Manager for Django Groups operations.

    This class provides utilities for working with Groups without any
    automatic assignment logic, following explicit assignment principles.
    """

    ROLE_GROUP_MAPPING = {
        "user": "User",
        "coach": "Coach",
        "doctor": "Doctor",
        "moderator": "Moderator",
        "admin": "Admin",
        "service": "Service",
        "influencer": "Influencer",
        "collector": "Collector",
    }

    @classmethod
    def get_group_by_name(cls, group_name: str) -> Optional[Group]:
        """
        Get Django Group instance by name.

        Args:
            group_name: Name of the group

        Returns:
            Group instance or None if group doesn't exist
        """
        try:
            return Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            logger.warning(f"Group not found: {group_name}")
            return None

    @classmethod
    def get_user_groups(cls, user) -> List[Group]:
        """
        Get all groups assigned to a user.

        Args:
            user: User instance

        Returns:
            List of Group instances
        """
        return list(user.groups.all())

    @classmethod
    def get_permissions_for_group(cls, group_name: str) -> Set[str]:
        """
        Get all permission codenames for a specific group.

        Args:
            group_name: Name of the group

        Returns:
            Set of permission codenames
        """
        group = cls.get_group_by_name(group_name)
        if not group:
            return set()

        return set(group.permissions.values_list("codename", flat=True))

    @classmethod
    def list_all_groups(cls) -> List[dict]:
        """
        List all groups with their metadata.

        Returns:
            List of dictionaries with group information
        """
        groups_info = []
        for group in Group.objects.all().order_by("name"):
            groups_info.append(
                {
                    "name": group.name,
                    "user_count": group.user_set.count(),
                    "permission_count": group.permissions.count(),
                    "permissions": list(
                        group.permissions.values_list("codename", flat=True)
                    ),
                }
            )
        return groups_info


class PermissionChecker:
    """
    Utility class for checking permissions with enhanced logic.

    This class provides methods for checking permissions that go beyond
    Django's basic has_perm() method, including object-level and contextual
    permission checks.
    """

    @staticmethod
    def can_modify_user(requesting_user, target_user) -> bool:
        """
        Check if requesting user can modify target user.

        Business Rules:
        - Users can modify their own profile
        - Users in Admin group can modify any user
        - Superusers can modify any user
        - Services can modify users based on API key scoping (handled in views)

        Args:
            requesting_user: User making the request
            target_user: User being modified

        Returns:
            bool: True if modification is allowed
        """

        if requesting_user.id == target_user.id:
            return True

        if requesting_user.is_superuser:
            return True

        if requesting_user.groups.filter(name="Admin").exists():
            return True

        if requesting_user.groups.filter(name="Service").exists():
            return True

        return False

    @staticmethod
    def can_moderate_content(user, content_obj) -> bool:
        """
        Check if user can moderate forum content.

        Args:
            user: User requesting moderation action
            content_obj: Forum content (Topic or Post)

        Returns:
            bool: True if moderation is allowed
        """

        if user.is_superuser:
            return True

        if user.groups.filter(name__in=["Admin", "Moderator"]).exists():
            return True

        if hasattr(content_obj, "author") and content_obj.author_id == user.id:
            return True

        return False

    @staticmethod
    def can_access_admin_panel(user) -> bool:
        """
        Check if user can access Django admin panel.

        Args:
            user: User instance

        Returns:
            bool: True if admin access is allowed
        """
        return user.is_staff and (
            user.is_superuser or user.groups.filter(name="Admin").exists()
        )


class GroupPermissionManager:
    """
    Manager for maintaining group permissions.

    This class provides methods for updating group permissions in a
    maintainable way, ensuring permissions stay in sync with business requirements.
    """

    @classmethod
    def update_group_permissions(
        cls, group_name: str, permission_codenames: List[str]
    ) -> bool:
        """
        Update permissions for a specific group.

        Args:
            group_name: Name of the group to update
            permission_codenames: List of permission codenames to assign

        Returns:
            bool: True if successful
        """
        try:
            with transaction.atomic():
                group = Group.objects.get(name=group_name)
                permissions = Permission.objects.filter(
                    codename__in=permission_codenames
                )

                group.permissions.set(permissions)

                logger.info(
                    f"Updated permissions for group '{group_name}': {permission_codenames}"
                )
                return True

        except Group.DoesNotExist:
            logger.error(f"Group '{group_name}' not found")
            return False
        except Exception as e:
            logger.error(f"Error updating permissions for group '{group_name}': {e}")
            return False

    @classmethod
    def add_permissions_to_group(
        cls, group_name: str, permission_codenames: List[str]
    ) -> bool:
        """
        Add additional permissions to a group without removing existing ones.

        Args:
            group_name: Name of the group
            permission_codenames: List of permission codenames to add

        Returns:
            bool: True if successful
        """
        try:
            group = Group.objects.get(name=group_name)
            permissions = Permission.objects.filter(codename__in=permission_codenames)

            group.permissions.add(*permissions)

            logger.info(
                f"Added permissions to group '{group_name}': {permission_codenames}"
            )
            return True

        except Group.DoesNotExist:
            logger.error(f"Group '{group_name}' not found")
            return False
        except Exception as e:
            logger.error(f"Error adding permissions to group '{group_name}': {e}")
            return False


def check_permission(user, permission: str, obj=None) -> bool:
    """
    Enhanced permission checking with object-level support.

    Args:
        user: User instance
        permission: Permission string (app.action_model format)
        obj: Optional object for object-level permissions

    Returns:
        bool: True if permission is granted
    """

    from django.contrib.auth.models import PermissionsMixin

    has_perm = PermissionsMixin.has_perm(user, permission, obj)

    if permission.endswith("change_user") and obj:
        return has_perm and PermissionChecker.can_modify_user(user, obj)

    if permission.startswith("apps_forum.") and obj:
        return has_perm and PermissionChecker.can_moderate_content(user, obj)

    return has_perm


def get_user_permission_context(user) -> dict:
    """
    Get comprehensive permission context for a user.

    Returns a dictionary with user's groups, key permissions, and capabilities
    for use in templates, APIs, and frontend applications.

    Args:
        user: User instance

    Returns:
        dict: Permission context
    """
    user_groups = [g.name for g in user.groups.all()]

    return {
        "groups": user_groups,
        "is_admin": user.is_superuser or "Admin" in user_groups,
        "is_moderator": "Moderator" in user_groups,
        "is_coach": "Coach" in user_groups,
        "is_doctor": "Doctor" in user_groups,
        "is_service": "Service" in user_groups,
        "is_influencer": "Influencer" in user_groups,
        "is_collector": "Collector" in user_groups,
        "can_access_admin": PermissionChecker.can_access_admin_panel(user),
        "permissions": list(user.get_all_permissions()),
    }
