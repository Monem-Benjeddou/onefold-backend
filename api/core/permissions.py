from rest_framework.permissions import BasePermission
from apps.accounts.auth.models import UserRoles


class RoleRequired(BasePermission):
    allowed_roles: set[str] = set()

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.role in self.allowed_roles


class AdminOnly(RoleRequired):
    allowed_roles = {UserRoles.ADMIN}


class StaffOrAdmin(RoleRequired):
    allowed_roles = {UserRoles.ADMIN, UserRoles.STAFF}


