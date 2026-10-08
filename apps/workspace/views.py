from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.learning import services as learning
from apps.learning.models import Enrollment
from apps.learning.serializers import EnrollmentSerializer
from apps.projects.serializers import ProjectSerializer

from . import services
from .models import OnboardingDraft
from .serializers import (
    DraftSerializer,
    OnboardingResultSerializer,
    OnboardingSerializer,
    OnboardingStateSerializer,
    WorkspaceSerializer,
)
from .starters import STARTERS


class Unavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_code = "path_unpublished"


class WorkspaceView(APIView):
    """The signed-in builder, their enrollment and their project, in one call."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=WorkspaceSerializer)
    def get(self, request):
        from apps.accounts.serializers import UserSerializer

        user = request.user
        enrollment = learning.get_active_enrollment(user)
        project = services.get_project(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "onboarding_complete": enrollment is not None and project is not None,
                "enrollment": EnrollmentSerializer(enrollment).data if enrollment else None,
                "project": ProjectSerializer(project).data if project else None,
            }
        )


class OnboardingView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=OnboardingStateSerializer)
    def get(self, request):
        draft = OnboardingDraft.objects.filter(user=request.user).first()
        return Response(
            {
                "complete": services.is_onboarded(request.user),
                "step": draft.step if draft else 1,
                "draft": draft.data if draft else {},
                "starters": STARTERS,
                "paces": [{"value": v, "label": label} for v, label in Enrollment.Pace.choices],
                "experiences": [
                    {"value": v, "label": label} for v, label in Enrollment.Experience.choices
                ],
            }
        )

    @extend_schema(
        request=OnboardingSerializer,
        responses={201: OnboardingResultSerializer, 200: OnboardingResultSerializer},
    )
    def post(self, request):
        """Finish onboarding: enroll and create the project in one transaction (idempotent)."""
        payload = OnboardingSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        try:
            enrollment, project, created = services.complete_onboarding(
                request.user,
                pace=data["pace"],
                experience=data["experience"],
                project_name=data["project_name"],
                project_idea=data["project_idea"],
                idea=data["idea"],
            )
        except learning.ProgressError as error:
            raise Unavailable(detail=str(error), code=error.code) from error
        return Response(
            {
                "enrollment": EnrollmentSerializer(enrollment).data,
                "project": ProjectSerializer(project).data,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class OnboardingDraftView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=DraftSerializer, responses={204: None})
    def put(self, request):
        payload = DraftSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        if not services.is_onboarded(request.user):
            services.save_draft(
                request.user, payload.validated_data["data"], payload.validated_data["step"]
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
