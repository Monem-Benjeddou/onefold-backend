from django.http import Http404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import PathVersion
from .serializers import (
    EnrollmentSerializer,
    EnrollRequestSerializer,
    PathOutlineSerializer,
    StepDetailSerializer,
)


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "conflict"


def raise_conflict(error):
    raise Conflict(detail=str(error), code=error.code)


def current_path_version():
    version = services.current_published_version()
    if version is None:
        raise Http404("No published path yet.")
    return version


def active_enrollment_or_404(user):
    enrollment = services.get_active_enrollment(user)
    if enrollment is None:
        raise Http404("You're not enrolled in a path yet.")
    return enrollment


class CurrentPathView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=PathOutlineSerializer)
    def get(self, request):
        version = (
            PathVersion.objects.prefetch_related("stations__steps")
            .select_related("path")
            .get(pk=current_path_version().pk)
        )
        return Response(PathOutlineSerializer(version).data)


class EnrollmentView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=EnrollmentSerializer)
    def get(self, request):
        return Response(EnrollmentSerializer(active_enrollment_or_404(request.user)).data)

    @extend_schema(request=EnrollRequestSerializer, responses=EnrollmentSerializer)
    def post(self, request):
        payload = EnrollRequestSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            enrollment, created = services.enroll(
                request.user, current_path_version(), pace=payload.validated_data["pace"]
            )
        except services.ProgressError as error:
            raise_conflict(error)
        return Response(
            EnrollmentSerializer(enrollment).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class StepMixin:
    permission_classes = [IsAuthenticated]

    def get_progress(self, request, slug):
        progress = services.get_progress(active_enrollment_or_404(request.user), slug)
        if progress is None:
            raise Http404("No such step in your path.")
        return progress


class StepDetailView(StepMixin, APIView):
    @extend_schema(responses=StepDetailSerializer)
    def get(self, request, slug):
        return Response(StepDetailSerializer(self.get_progress(request, slug)).data)

    @extend_schema(request=StepDetailSerializer, responses=StepDetailSerializer)
    def patch(self, request, slug):
        """Save where the builder is in the step, so Continue resumes there."""
        progress = self.get_progress(request, slug)
        serializer = StepDetailSerializer(
            progress, data={"last_position": request.data.get("last_position")}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class StepStartView(StepMixin, APIView):
    @extend_schema(request=None, responses=StepDetailSerializer)
    def post(self, request, slug):
        try:
            progress = services.start_step(self.get_progress(request, slug))
        except services.ProgressError as error:
            raise_conflict(error)
        return Response(StepDetailSerializer(progress).data)


class StepCompleteView(StepMixin, APIView):
    @extend_schema(request=None, responses=StepDetailSerializer)
    def post(self, request, slug):
        try:
            progress = services.complete_step(self.get_progress(request, slug))
        except services.ProgressError as error:
            raise_conflict(error)
        return Response(StepDetailSerializer(progress).data)
