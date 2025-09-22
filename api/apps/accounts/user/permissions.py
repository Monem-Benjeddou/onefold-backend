from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _


class IsBusinessAdminOrNeoAdmin(BasePermission):
    """
    Permission class to check if user is a business admin or moderator.

    Uses Django Groups-based RBAC system for proper permission checking.
    Only users in Admin or Moderator groups are granted access.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        return (
            request.user.is_superuser
            or request.user.groups.filter(name__in=["Admin", "Moderator"]).exists()
        )


class CanManageUsers(BasePermission):
    """
    Permission class for user management operations.

    Uses Django's permission system through Groups:
    - Superusers can manage any user
    - Users in Admin group can manage users
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        return (
            request.user.is_superuser
            or request.user.groups.filter(name="Admin").exists()
        )

    def has_object_permission(self, request, view, obj):
        """Check object-level user management permissions"""

        return request.user.has_perm("_user.change_user", obj)


class IsCardCreatorOrAdminOrSalesman(BasePermission):
    """
    Permission class for card creation and issuer management operations.

    Allows access to users with the following roles:
    - card_creator: Users with card creator role
    - admin: Administrator users
    - salesman: Sales team members
    - moderator: Moderator users (for backward compatibility)
    - superuser: System superusers

    Also checks for Admin or Moderator groups for users with appropriate roles.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.user.is_superuser:
            return True

        allowed_roles = ["card_creator", "admin", "salesman", "moderator"]
        if request.user.role in allowed_roles:
            return True

        return request.user.groups.filter(name__in=["Admin", "Moderator"]).exists()


class IsCardCreatorOrAdmin(BasePermission):
    """
    Permission class for collection creation operations.

    Allows access to users with the following roles:
    - card_creator: Users with card creator role
    - issuer: Issuer users (primary card creators)
    - influencer: Influencer users (primary collection creators)
    - admin: Administrator users
    - superuser: System superusers

    More restrictive than IsCardCreatorOrAdminOrSalesman for sensitive operations.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.user.is_superuser:
            return True

        allowed_roles = ["card_creator", "issuer", "influencer", "admin"]
        if request.user.role in allowed_roles:
            return True

        return request.user.groups.filter(name="Admin").exists()


class IsSalesmanOrAdminOrSuperAdmin(BasePermission):
    """
    Permission class for payment and order management operations.

    Allows access to users with the following roles:
    - salesman: Sales team members who can manage orders and transactions
    - admin: Administrator users with full access
    - superuser: System superusers

    This permission is used for:
    - Viewing and managing orders
    - Viewing transactions
    - Performing admin actions on payment-related resources
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.user.is_superuser:
            return True

        allowed_roles = ["salesman", "admin"]
        if request.user.role in allowed_roles:
            return True

        return request.user.groups.filter(name="Admin").exists()
