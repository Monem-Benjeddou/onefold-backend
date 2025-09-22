from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from django.utils.translation import gettext as _

from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit
from ..serializers import CreateFileSerializer, ExtendedFileSerializer


@extend_schema(tags=["Files"])
class FileCreateView(CreateAPIView):
    """
    API view for creating new files.
    Handles file upload with validation and type detection.
    """

    serializer_class = CreateFileSerializer
    permission_classes = [IsAuthenticated]

    @api_error_handler
    @dynamic_rate_limit(default_rate=10, default_period=60)
    @extend_schema(
        description="Upload a new file",
        request=CreateFileSerializer,
        responses={
            201: ExtendedFileSerializer,
            400: {"description": _("Bad Request")},
            406: {"description": _("Not Acceptable - Invalid file type")},
            429: {"description": _("Too Many Requests")},
        },
    )
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
