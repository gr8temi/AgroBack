from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ReportConfig, Question, DailyReport
from .serializers import (
    ReportConfigSerializer, QuestionSerializer, 
    DailyReportSerializer, DailyReportSubmissionSerializer
)

class ReportConfigViewSet(viewsets.ModelViewSet):
    serializer_class = ReportConfigSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        print(f"DEBUG: ReportConfig List - User: {user}, Farm: {getattr(user, 'farm', 'None')}")
        if not user.farm:
            return ReportConfig.objects.none()
        return ReportConfig.objects.filter(farm=user.farm)
    
    def create(self, request, *args, **kwargs):
        user = self.request.user
        if not user.farm:
            return Response({"detail": "User has no farm"}, status=status.HTTP_400_BAD_REQUEST)
            
        # Check if config exists
        existing_config = ReportConfig.objects.filter(farm=user.farm).first()
        
        if existing_config:
            # Update existing
            serializer = self.get_serializer(existing_config, data=request.data, partial=True)
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
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        print(f"DEBUG: Question List - User: {user}, Farm: {getattr(user, 'farm', 'None')}")
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
        print(f"DEBUG: DailyReport List - Request User: {user}, Farm: {getattr(user, 'farm', 'None')}")
        if not user.farm:
            print("DEBUG: User has no farm")
            return DailyReport.objects.none()
        qs = DailyReport.objects.filter(farm=user.farm)
        print(f"DEBUG: Found {qs.count()} reports for farm {user.farm}")
        return qs

    def get_serializer_class(self):
        if self.action == 'create':
            return DailyReportSubmissionSerializer
        return DailyReportSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, farm=self.request.user.farm)
