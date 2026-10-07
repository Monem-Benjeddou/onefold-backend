from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.projects.models import Project

from . import services
from .models import CheckRun
from .serializers import CheckRequestSerializer, CheckRunSerializer
from .tasks import run_check_task


class CheckRequestRejected(APIException):
    def __init__(self, error):
        self.status_code = error.status
        super().__init__(detail=str(error), code=error.code)


class ProjectCheckListCreateView(generics.ListCreateAPIView):
    """List a project's check runs, or run a step's check ("Check my work")."""

    serializer_class = CheckRunSerializer
    permission_classes = [IsAuthenticated]

    def get_project(self):
        return get_object_or_404(Project, pk=self.kwargs["project_id"], user=self.request.user)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return CheckRun.objects.none()
        runs = CheckRun.objects.filter(project=self.get_project()).select_related("step")
        step = self.request.query_params.get("step")
        return runs.filter(step__slug=step) if step else runs

    @extend_schema(parameters=[OpenApiParameter("step", str, description="Filter by step slug")])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        request=CheckRequestSerializer,
        responses={202: CheckRunSerializer, 200: CheckRunSerializer},
        parameters=[
            OpenApiParameter(
                "Idempotency-Key",
                str,
                OpenApiParameter.HEADER,
                description="Repeat a request safely; the same key returns the same run.",
            )
        ],
    )
    def post(self, request, *args, **kwargs):
        payload = CheckRequestSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        key = request.headers.get("Idempotency-Key", "")[:64]
        try:
            run, created = services.request_check(
                self.get_project(), payload.validated_data["step"], idempotency_key=key
            )
        except services.CheckRequestError as error:
            raise CheckRequestRejected(error)
        if created:
            transaction.on_commit(lambda: run_check_task.delay(str(run.pk)))
        return Response(
            CheckRunSerializer(run).data,
            status=status.HTTP_202_ACCEPTED if created else status.HTTP_200_OK,
        )


class CheckRunDetailView(generics.RetrieveAPIView):
    """Poll one check run until it's finished."""

    serializer_class = CheckRunSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CheckRun.objects.filter(project__user=self.request.user).select_related("step")
