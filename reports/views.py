from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ReportConfig, Question, DailyReport
from .serializers import (
    ReportConfigSerializer,
    QuestionSerializer,
    DailyReportSerializer,
    DailyReportSubmissionSerializer,
)
from core.utils import send_push_notification


from core.permissions import IsManager


class ReportConfigViewSet(viewsets.ModelViewSet):
    serializer_class = ReportConfigSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.IsAuthenticated()]
        return [IsManager()]

    def get_queryset(self):
        user = self.request.user
        if not user.farm:
            return ReportConfig.objects.none()
        return ReportConfig.objects.filter(farm=user.farm)

    def create(self, request, *args, **kwargs):
        user = self.request.user
        if not user.farm:
            return Response(
                {"detail": "User has no farm"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Check if config exists
        existing_config = ReportConfig.objects.filter(farm=user.farm).first()

        if existing_config:
            # Update existing
            serializer = self.get_serializer(
                existing_config, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        # Create new
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = self.request.user
        if not user.farm:
            raise serializers.ValidationError("User has no farm")
        serializer.save(farm=user.farm)


class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.IsAuthenticated()]
        return [IsManager()]

    def get_queryset(self):
        user = self.request.user
        if not user.farm:
            return Question.objects.none()
        return Question.objects.filter(config__farm=user.farm)

    def perform_create(self, serializer):
        user = self.request.user
        if not user.farm:
            raise serializers.ValidationError("User has no farm")

        # Ensure config exists
        config, created = ReportConfig.objects.get_or_create(farm=user.farm)
        serializer.save(config=config)


class DailyReportViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.farm:
            return DailyReport.objects.none()
        qs = DailyReport.objects.filter(farm=user.farm)
        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return DailyReportSubmissionSerializer
        return DailyReportSerializer

    def perform_create(self, serializer):
        report = serializer.save(user=self.request.user, farm=self.request.user.farm)

        # Notify managers and superusers on the farm
        recipients = report.farm.members.filter(role__in=["manager", "superuser"])
        send_push_notification(
            recipients,
            title="New Report Submitted",
            message=f"{self.request.user.get_full_name() or self.request.user.username} submitted the daily report for {report.reference_date}.",
            data={"type": "report_submitted", "report_id": report.id},
        )
