from django.urls import path

from apps.accounts.user.views import (
    CreateUserView,
    UpdateUserView,
    DeleteUserView,
    RetrieveUserView,
    ListUsersView,
    UpdateRoleView,
    ExportUsersView,
    ActivateUserView,
    DeactivateUserView,
    BanUserView,
    UnbanUserView,
    AdminStatsView,
    SelfDeactivationView,
    AccountStatusView,
)
from apps.relationships.views.user_follow import UserFollowView

urlpatterns = [
    path("create/", CreateUserView.as_view(), name="create-user"),
    path("<uuid:pk>/update/", UpdateUserView.as_view(), name="update-user"),
    path("<uuid:pk>/", RetrieveUserView.as_view(), name="retrieve-user"),
    path("delete/<uuid:pk>/", DeleteUserView.as_view(), name="delete-user"),
    path("", ListUsersView.as_view(), name="list-user"),
    path("<uuid:pk>/update-role/", UpdateRoleView.as_view(), name="update-role"),
    path("export/", ExportUsersView.as_view(), name="export-users"),
    path("<uuid:pk>/activate/", ActivateUserView.as_view(), name="admin-activate-user"),
    path(
        "<uuid:pk>/deactivate/",
        DeactivateUserView.as_view(),
        name="admin-deactivate-user",
    ),
    path("<uuid:pk>/ban/", BanUserView.as_view(), name="admin-ban-user"),
    path("<uuid:pk>/unban/", UnbanUserView.as_view(), name="admin-unban-user"),
    path("stats/", AdminStatsView.as_view(), name="admin-stats"),
    path("me/deactivate/", SelfDeactivationView.as_view(), name="self-deactivate"),
    path("me/status/", AccountStatusView.as_view(), name="account-status"),
    path("<uuid:pk>/follow/", UserFollowView.as_view(), name="user-follow"),
]
