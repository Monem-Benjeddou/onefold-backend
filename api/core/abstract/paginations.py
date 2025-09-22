from rest_framework.pagination import (
    LimitOffsetPagination,
    PageNumberPagination,
    CursorPagination,
)
from rest_framework.response import Response
from django.utils.encoding import force_str


class MetaLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 5
    limit_query_param = "limit"
    max_limit = 1000
    offset_query_param = "offset"
    page_size_query_param = "page_size"

    def get_paginated_response(self, data):
        current_offset = self.offset
        current_limit = self.get_limit(self.request)

        page_size = int(self.request.query_params.get("page_size", current_limit))
        current_limit = min(max(0, page_size), self.max_limit)

        total_count = self.count

        current_page_number = (
            (current_offset // current_limit + 1) if current_limit > 0 else 1
        )
        total_pages = (
            (total_count // current_limit)
            + (1 if total_count % current_limit != 0 else 0)
            if current_limit > 0
            else 1
        )
        next_page_number = (
            current_page_number + 1
            if current_offset + current_limit < total_count
            else None
        )
        previous_page_number = current_page_number - 1 if current_offset > 0 else None

        return Response(
            {
                "meta": {
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                    "next_page_number": next_page_number,
                    "previous_page_number": previous_page_number,
                    "limit": current_limit,
                    "offset": current_offset,
                    "count": total_count,
                    "total_pages": total_pages,
                    "current_page_number": current_page_number,
                },
                "results": data,
            }
        )


class MetaPageNumberPagination(PageNumberPagination):
    page_size = 5
    page_query_param = "page"
    page_size_query_param = "limit"
    max_page_size = 1000

    def get_page_size(self, request):
        try:
            page_size = int(
                request.query_params.get(self.page_size_query_param, self.page_size)
            )
            if page_size > self.max_page_size:
                return self.max_page_size
            return page_size
        except (TypeError, ValueError):
            return self.page_size

    def get_paginated_response(self, data):
        current_page_number = self.page.number
        total_pages = self.page.paginator.num_pages
        total_count = self.page.paginator.count
        page_size = self.get_page_size(self.request)

        next_page_number = current_page_number + 1 if self.page.has_next() else None
        previous_page_number = (
            current_page_number - 1 if self.page.has_previous() else None
        )

        return Response(
            {
                "meta": {
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                    "next_page_number": next_page_number,
                    "previous_page_number": previous_page_number,
                    "limit": page_size,
                    "count": total_count,
                    "total_pages": total_pages,
                    "current_page_number": current_page_number,
                },
                "results": data,
            }
        )


class InfluencerCursorPagination(CursorPagination):
    """
    High-performance cursor pagination for influencer lists with large datasets.
    Provides stable, scalable pagination that works well with real-time updates.
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    ordering = "-created"
    cursor_query_param = "cursor"
    offset_cutoff = 1000

    def get_page_size(self, request):
        """Get page size with validation"""
        try:
            page_size = int(
                request.query_params.get(self.page_size_query_param, self.page_size)
            )
            if page_size > self.max_page_size:
                return self.max_page_size
            return max(1, page_size)
        except (TypeError, ValueError):
            return self.page_size

    def get_paginated_response(self, data):
        """Enhanced cursor pagination response with metadata"""
        has_next = self.has_next
        has_previous = self.has_previous

        position_info = {}
        if hasattr(self, "cursor") and self.cursor:
            position_info = {
                "has_more_recent": has_previous,
                "has_more_older": has_next,
                "cursor_position": force_str(self.cursor),
            }

        return Response(
            {
                "meta": {
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                    "has_next": has_next,
                    "has_previous": has_previous,
                    "page_size": self.get_page_size(self.request),
                    "ordering": self.ordering,
                    **position_info,
                },
                "results": data,
            }
        )


class HybridInfluencerPagination(MetaPageNumberPagination):
    """
    Hybrid pagination that uses page-based for small datasets
    and cursor-based for large datasets to optimize performance.
    """

    page_size = 20
    max_page_size = 100
    cursor_cutoff = 1000

    def __init__(self):
        super().__init__()
        self._cursor_pagination = None

    def paginate_queryset(self, queryset, request, view=None):
        """Decide between page-based and cursor-based pagination"""
        self.request = request

        total_count = queryset.count()

        if total_count > self.cursor_cutoff and self._should_use_cursor(request):

            if not self._cursor_pagination:
                self._cursor_pagination = InfluencerCursorPagination()
                self._cursor_pagination.page_size = self.get_page_size(request)

            return self._cursor_pagination.paginate_queryset(queryset, request, view)
        else:

            return super().paginate_queryset(queryset, request, view)

    def _should_use_cursor(self, request):
        """Determine if cursor pagination should be used"""

        return (
            "cursor" in request.query_params
            or request.query_params.get("page", "1") == "1"
        )

    def get_paginated_response(self, data):
        """Return appropriate paginated response"""
        if self._cursor_pagination and hasattr(self._cursor_pagination, "page"):
            return self._cursor_pagination.get_paginated_response(data)
        return super().get_paginated_response(data)
