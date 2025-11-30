from django.db import transaction

from rest_framework import viewsets, permissions

from core.permissions import IsManager, IsStaff

from .models import Flock, FeedLog, HealthLog, EggCollection
from .serializers import FlockSerializer, FeedLogSerializer, HealthLogSerializer, EggCollectionSerializer

class FlockViewSet(viewsets.ModelViewSet):
    serializer_class = FlockSerializer
    # permission_classes = [IsManager] # Old: Only managers
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsStaff] # Staff can view
        else:
            permission_classes = [IsManager] # Only managers can create/edit/delete
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        return Flock.objects.filter(farm=self.request.user.farm)

    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save(user=self.request.user, farm=self.request.user.farm)

class FeedLogViewSet(viewsets.ModelViewSet):
    serializer_class = FeedLogSerializer
    permission_classes = [IsStaff] # Staff can add logs

    def get_queryset(self):
        return FeedLog.objects.filter(flock__farm=self.request.user.farm)

class HealthLogViewSet(viewsets.ModelViewSet):
    serializer_class = HealthLogSerializer
    permission_classes = [IsStaff] # Staff can add logs

    def get_queryset(self):
        return HealthLog.objects.filter(flock__farm=self.request.user.farm)

class EggCollectionViewSet(viewsets.ModelViewSet):
    serializer_class = EggCollectionSerializer
    permission_classes = [IsStaff] # Staff can add logs

    def get_queryset(self):
        return EggCollection.objects.filter(flock__farm=self.request.user.farm)
