from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FlockViewSet, FeedLogViewSet, HealthLogViewSet, EggCollectionViewSet

router = DefaultRouter()
router.register(r'flocks', FlockViewSet, basename='flock')
router.register(r'feed-logs', FeedLogViewSet, basename='feed-log')
router.register(r'health-logs', HealthLogViewSet, basename='health-log')
router.register(r'egg-collections', EggCollectionViewSet, basename='egg-collection')

urlpatterns = [
    path('', include(router.urls)),
]
