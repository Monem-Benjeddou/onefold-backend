from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        return bool(getattr(user, "is_staff", False) or getattr(user, "role", "") == "admin")


class IsFounder(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        return getattr(user, "role", "") == "founder"


class IsReviewer(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        # Reviewer is strictly read-only
        if request.method not in SAFE_METHODS:
            return False
        return getattr(user, "role", "") == "reviewer"


class StartupAccessPermission(BasePermission):
    """
    Admin: full access
    Founder: full access to own startups (write), can read public/own
    Reviewer: read-only
    """

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        role = getattr(user, "role", "")
        if getattr(user, "is_staff", False) or role == "admin":
            return True
        if role == "reviewer":
            return request.method in SAFE_METHODS
        if role == "founder":
            return True
        # Default deny for other roles on company resources
        return False

    def has_object_permission(self, request, view, obj):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        role = getattr(user, "role", "")
        if getattr(user, "is_staff", False) or role == "admin":
            return True
        if role == "reviewer":
            return request.method in SAFE_METHODS
        if role == "founder":
            # Founders can write only their own startups; read allowed if public/own
            if request.method in SAFE_METHODS:
                return True
            return getattr(obj, "primary_founder_id", None) == getattr(user, "id", None)
        return False


class IsFounderOrMember(BasePermission):
    """
    Allows access if the user is the startup's primary founder or a member of that startup.
    Admin/staff always allowed.
    For create actions (no object yet), validates against provided startup id in request.data.
    """

    def _get_startup_from_obj(self, obj):
        # Support StartupProfile, StartupServiceProduct, CompanyMember, TargetedMarket, etc.
        if hasattr(obj, "startup"):
            return getattr(obj, "startup")
        return obj if hasattr(obj, "primary_founder_id") else None

    def _is_founder_or_member(self, user, startup):
        if not startup:
            return False
        if getattr(startup, "primary_founder_id", None) == getattr(user, "id", None):
            return True
        try:
            from apps.company.models import CompanyMember

            return CompanyMember.objects.filter(startup=startup, user=user).exists()
        except Exception:
            return False

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        if getattr(user, "is_staff", False) or getattr(user, "role", "") == "admin":
            return True
        # For create, require startup id in payload and validate membership
        if request.method not in SAFE_METHODS and getattr(view, "action", None) == "create":
            startup_id = request.data.get("startup")
            if not startup_id:
                return False
            try:
                from apps.company.models import StartupProfile

                startup = StartupProfile.objects.get(id=startup_id)
            except Exception:
                return False
            return self._is_founder_or_member(user, startup)
        return True

    def has_object_permission(self, request, view, obj):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        if getattr(user, "is_staff", False) or getattr(user, "role", "") == "admin":
            return True
        startup = self._get_startup_from_obj(obj)
        return self._is_founder_or_member(user, startup)


