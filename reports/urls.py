from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportConfigViewSet, DailyReportViewSet, QuestionViewSet

router = DefaultRouter()
router.register(r'config', ReportConfigViewSet, basename='report-config')
router.register(r'submissions', DailyReportViewSet, basename='report-submission')
router.register(r'questions', QuestionViewSet, basename='report-question')

urlpatterns = [
    path('', include(router.urls)),
]
