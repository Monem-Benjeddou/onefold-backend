from django_filters import rest_framework as filters
from django.utils.translation import gettext_lazy as _
from apps.accounts.user.models import User
from apps.accounts.user.constants import ROLE_CHOICES


class UserFilter(filters.FilterSet):
    """
    Filter for User model with comprehensive filtering options.
    """

    role = filters.MultipleChoiceFilter(
        field_name="role",
        choices=ROLE_CHOICES,
        label=_("User Roles"),
        help_text=_("Filter users with any of these roles"),
        conjoined=False,
    )

    email = filters.CharFilter(
        lookup_expr="icontains",
        label=_("Email"),
        help_text=_("Filter users containing this text in email"),
    )

    fullname = filters.CharFilter(
        lookup_expr="icontains",
        label=_("Full Name"),
        help_text=_("Filter users containing this text in full name"),
    )

    username = filters.CharFilter(
        lookup_expr="icontains",
        label=_("Username"),
        help_text=_("Filter users containing this text in username"),
    )

    is_active = filters.BooleanFilter(
        label=_("Is Active"), help_text=_("Filter active/inactive users")
    )

    is_staff = filters.BooleanFilter(
        label=_("Is Staff"), help_text=_("Filter staff users")
    )

    created_after = filters.DateFilter(
        field_name="created",
        lookup_expr="gte",
        label=_("Created After"),
        help_text=_("Filter users created after this date (format: YYYY-MM-DD)"),
    )

    created_before = filters.DateFilter(
        field_name="created",
        lookup_expr="lte",
        label=_("Created Before"),
        help_text=_("Filter users created before this date (format: YYYY-MM-DD)"),
    )

    class Meta:
        model = User
        fields = [
            "role",
            "email",
            "fullname",
            "username",
            "is_active",
            "is_staff",
            "created_after",
            "created_before",
        ]
