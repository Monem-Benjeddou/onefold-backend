from django_filters import rest_framework as filters
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from apps.accounts.user.models import User
from apps.accounts.user.constants import ROLE_CHOICES
from django.utils import timezone
import datetime
from datetime import timedelta


class UserFilter(filters.FilterSet):
    """
    Filter for User model with comprehensive filtering options.
    """

    role_exact = filters.ChoiceFilter(
        field_name="role",
        choices=ROLE_CHOICES,
        label=_("User Role (Exact)"),
        help_text=_("Filter by exact user role"),
        lookup_expr="exact",
    )

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

    email_exact = filters.CharFilter(
        field_name="email",
        lookup_expr="exact",
        label=_("Exact Email"),
        help_text=_("Filter users with this exact email"),
    )

    email_domain = filters.CharFilter(
        field_name="email",
        method="filter_email_domain",
        label=_("Email Domain"),
        help_text=_("Filter users by email domain (e.g., 'gmail.com')"),
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

    username_exact = filters.CharFilter(
        field_name="username",
        lookup_expr="exact",
        label=_("Exact Username"),
        help_text=_("Filter users with this exact username"),
    )

    is_active = filters.BooleanFilter(
        method="filter_is_active",
        label=_("Is Active"),
        help_text=_("Filter active/inactive users"),
    )

    is_staff = filters.BooleanFilter(
        label=_("Is Staff"), help_text=_("Filter staff users")
    )

    is_superuser = filters.BooleanFilter(
        label=_("Is Superuser"), help_text=_("Filter superuser accounts")
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

    last_login_after = filters.DateFilter(
        field_name="last_login",
        lookup_expr="gte",
        label=_("Last Login After"),
        help_text=_("Filter users who logged in after this date (format: YYYY-MM-DD)"),
    )

    last_login_before = filters.DateFilter(
        field_name="last_login",
        lookup_expr="lte",
        label=_("Last Login Before"),
        help_text=_("Filter users who logged in before this date (format: YYYY-MM-DD)"),
    )

    has_logged_in = filters.BooleanFilter(
        field_name="last_login",
        lookup_expr="isnull",
        exclude=True,
        label=_("Has Logged In"),
        help_text=_("Filter users who have logged in at least once"),
    )

    search = filters.CharFilter(
        method="filter_search",
        label=_("Search"),
        help_text=_("Search in username, email, and fullname"),
    )

    def filter_email_domain(self, queryset, name, value):
        """Filter users by email domain"""
        return queryset.filter(email__iendswith=f"@{value}")

    def filter_search(self, queryset, name, value):
        """Search in multiple fields"""
        return queryset.filter(
            Q(username__icontains=value)
            | Q(email__icontains=value)
            | Q(fullname__icontains=value)
        )

    def filter_is_active(self, queryset, name, value):
        """Filter users by active status based on last_login and created date"""
        if value:
            thirty_days_ago = timezone.now() - timedelta(days=30)
            return queryset.filter(
                Q(last_login__gte=thirty_days_ago) | Q(created__gte=thirty_days_ago)
            )
        else:
            thirty_days_ago = timezone.now() - timedelta(days=30)
            return queryset.filter(
                Q(last_login__isnull=True) & Q(created__lt=thirty_days_ago)
            )

    def filter_inactive_only(self, queryset, name, value):
        """Only include inactive users if value is True"""
        if value:
            thirty_days_ago = timezone.now() - timedelta(days=30)
            return queryset.filter(
                Q(last_login__isnull=True) & Q(created__lt=thirty_days_ago)
            )
        return queryset

    class Meta:
        model = User
        fields = [
            "role_exact",
            "role",
            "email",
            "email_exact",
            "email_domain",
            "fullname",
            "username",
            "username_exact",
            "is_active",
            "is_staff",
            "is_superuser",
            "created_after",
            "created_before",
            "last_login_after",
            "last_login_before",
            "has_logged_in",
            "search",
        ]


class UserExportFilter(UserFilter):
    """
    Extended filter for User exports with additional options.
    """

    exclude_staff = filters.BooleanFilter(
        method="filter_exclude_staff",
        label=_("Exclude Staff"),
        help_text=_("Exclude staff users from export"),
    )

    exclude_superusers = filters.BooleanFilter(
        method="filter_exclude_superusers",
        label=_("Exclude Superusers"),
        help_text=_("Exclude superuser accounts from export"),
    )

    inactive_only = filters.BooleanFilter(
        method="filter_inactive_only",
        label=_("Inactive Only"),
        help_text=_("Only include inactive users in export"),
    )

    never_logged_in = filters.BooleanFilter(
        method="filter_never_logged_in",
        label=_("Never Logged In"),
        help_text=_("Only include users who have never logged in"),
    )

    created_this_month = filters.BooleanFilter(
        method="filter_created_this_month",
        label=_("Created This Month"),
        help_text=_("Only include users created in the current month"),
    )

    created_this_year = filters.BooleanFilter(
        method="filter_created_this_year",
        label=_("Created This Year"),
        help_text=_("Only include users created in the current year"),
    )

    def filter_exclude_staff(self, queryset, name, value):
        """Exclude staff users if value is True"""
        if value:
            return queryset.filter(is_staff=False)
        return queryset

    def filter_exclude_superusers(self, queryset, name, value):
        """Exclude superusers if value is True"""
        if value:
            return queryset.filter(is_superuser=False)
        return queryset

    def filter_never_logged_in(self, queryset, name, value):
        """Only include users who have never logged in if value is True"""
        if value:
            return queryset.filter(last_login__isnull=True)
        return queryset

    def filter_created_this_month(self, queryset, name, value):
        """Only include users created in the current month if value is True"""
        if value:
            now = timezone.now()
            return queryset.filter(created__year=now.year, created__month=now.month)
        return queryset

    def filter_created_this_year(self, queryset, name, value):
        """Only include users created in the current year if value is True"""
        if value:
            now = timezone.now()
            return queryset.filter(created__year=now.year)
        return queryset

    class Meta(UserFilter.Meta):
        fields = UserFilter.Meta.fields + [
            "exclude_staff",
            "exclude_superusers",
            "inactive_only",
            "never_logged_in",
            "created_this_month",
            "created_this_year",
        ]
