from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema

from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit
from apps.accounts.user.models import User
from apps.accounts.user.permissions import IsBusinessAdminOrNeoAdmin


@extend_schema(tags=["Admin"])
class AdminStatsView(APIView):
    """
    Admin view for retrieving dashboard statistics.

    This view provides comprehensive statistics for the admin dashboard
    including user counts, forum statistics, and content metrics.
    """

    permission_classes = [IsAuthenticated, IsBusinessAdminOrNeoAdmin]

    @api_error_handler
    @dynamic_rate_limit(default_rate=20, default_period=60)
    @extend_schema(
        description="Get admin dashboard statistics",
        responses={
            200: {"description": "Admin statistics retrieved successfully"},
            403: {"description": "Permission denied"},
        },
    )
    def get(self, request, *args, **kwargs):
        """Get admin dashboard statistics"""
        from django.utils import timezone

        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        user_stats = self._get_user_statistics(start_of_month)

        forum_stats, content_stats = self._get_forum_statistics(start_of_month)

        return Response(
            {
                "users": user_stats,
                "forums": forum_stats,
                "content": content_stats,
                "generated_at": now.isoformat(),
            }
        )

    def _get_user_statistics(self, start_of_month):
        """Get user-related statistics"""
        return {
            "total": User.objects.count(),
            "active": User.objects.filter(is_active=True).count(),
            "staff": User.objects.filter(is_staff=True).count(),
            "superusers": User.objects.filter(is_superuser=True).count(),
            "new_this_month": User.objects.filter(created__gte=start_of_month).count(),
        }

    def _get_forum_statistics(self, start_of_month):
        """Get forum and content statistics"""
        forum_stats = {
            "total": 0,
            "active": 0,
            "inactive": 0,
            "categories": 0,
            "links": 0,
        }
        content_stats = {
            "total_topics": 0,
            "total_posts": 0,
            "pending_moderation": 0,
            "this_month_topics": 0,
            "this_month_posts": 0,
        }

        try:
            from apps.forum.models import Forum, Topic, Post

            forum_stats = {
                "total": Forum.objects.count(),
                "active": Forum.objects.filter(is_active=True).count(),
                "inactive": Forum.objects.filter(is_active=False).count(),
                "categories": Forum.objects.filter(type="category").count(),
                "links": Forum.objects.filter(type="link").count(),
            }

            content_stats = {
                "total_topics": Topic.objects.count(),
                "total_posts": Post.objects.count(),
                "pending_moderation": (
                    Topic.objects.filter(approved=False).count()
                    + Post.objects.filter(approved=False).count()
                ),
                "this_month_topics": Topic.objects.filter(
                    created__gte=start_of_month
                ).count(),
                "this_month_posts": Post.objects.filter(
                    created__gte=start_of_month
                ).count(),
            }
        except ImportError:
            pass

        return forum_stats, content_stats
