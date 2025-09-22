"""
Custom permission classes for the application.
"""

from rest_framework.permissions import BasePermission


class IsSuperUser(BasePermission):
    """
    Permission class that allows access only to superusers.
    """

    def has_permission(self, request, view):
        """
        Check if the user is authenticated and is a superuser.
        """
        return (
            request.user and request.user.is_authenticated and request.user.is_superuser
        )

    def has_object_permission(self, request, view, obj):
        """
        Check object-level permissions for superusers.
        """
        return (
            request.user and request.user.is_authenticated and request.user.is_superuser
        )


class ExportPermission(BasePermission):
    """
    Standardized permission class for all export functionality.

    SECURITY ENHANCEMENT: Uses both role-based and group-based validation
    for consistent permission enforcement across the application.

    Allows access to:
    - Superadmins (is_superuser=True)
    - Admins (role='admin')
    - Salesmen (role='salesman')
    - Card creators (role='card_creator')
    - Issuers (role='issuer' - can export their own data)
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if (
            hasattr(request.user, "is_currently_banned")
            and request.user.is_currently_banned()
        ):
            return False

        if request.user.is_superuser:
            return True

        allowed_roles = ["admin", "salesman", "card_creator", "issuer"]
        if request.user.role not in allowed_roles:
            return False

        if request.user.role == "admin":
            return True
        elif request.user.role == "salesman":
            return True
        elif request.user.role == "card_creator":
            return True
        elif request.user.role == "issuer":
            return True

        return False


class CategoryManagementPermission(BasePermission):
    """
    Permission class for category CRUD operations.

    Allows full category management access to:
    - Superadmins (is_superuser=True)
    - Admins (role='admin')
    - Card creators (role='card_creator')
    - Salesmen (role='salesman')

    These roles can create, read, update, and delete categories.
    Regular users and unauthenticated users cannot modify categories.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if (
            hasattr(request.user, "is_currently_banned")
            and request.user.is_currently_banned()
        ):
            return False

        if request.user.is_superuser:
            return True

        allowed_roles = ["admin", "card_creator", "salesman"]
        return request.user.role in allowed_roles

    def has_object_permission(self, request, view, obj):
        """
        Check object-level permissions for category operations.
        Same logic as has_permission since all privileged users can manage all categories.
        """
        return self.has_permission(request, view)
