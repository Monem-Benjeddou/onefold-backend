from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from django.utils.translation import gettext as _

from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit
from core.abstract.paginations import MetaPageNumberPagination
from ..models import File
from ..serializers import ExtendedFileSerializer, CreateFileSerializer


@extend_schema_view(
    get=extend_schema(
        tags=["Files"],
        description="Get list of all files",
        responses={
            200: ExtendedFileSerializer(many=True),
            429: {"description": _("Too Many Requests")},
        },
    ),
    post=extend_schema(
        tags=["Files"],
        description="Upload a new file",
        request=CreateFileSerializer,
        responses={
            201: ExtendedFileSerializer,
            400: {"description": _("Bad Request")},
            406: {"description": _("Not Acceptable - Invalid file type")},
            429: {"description": _("Too Many Requests")},
        },
    ),
)
class FileListView(ListCreateAPIView):
    """
    API view for listing all files.
    Provides paginated list of files with metadata.
    """

    queryset = File.objects.all().order_by("-created")
    serializer_class = ExtendedFileSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = MetaPageNumberPagination

    def get_serializer_class(self):
        """
        Return the serializer class based on the request method.
        """
        if hasattr(self, "request") and self.request.method == "POST":
            return CreateFileSerializer
        return ExtendedFileSerializer

    @api_error_handler
    @dynamic_rate_limit(default_rate=20, default_period=60)
    def get(self, request, *args, **kwargs):
        """
        Retrieve a paginated list of all files.
        Returns files ordered by creation date (newest first).
        """
        return self.list(request, *args, **kwargs)

    @api_error_handler
    @dynamic_rate_limit(default_rate=10, default_period=60)
    def post(self, request, *args, **kwargs):
        """
        Upload a new file.
        Validates file type and creates a new file record.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file_instance = serializer.save()

        response_serializer = ExtendedFileSerializer(
            file_instance, context={"request": request}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
