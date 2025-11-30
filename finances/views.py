from django.db import transaction

from rest_framework import viewsets, permissions

from core.permissions import IsManager

from .models import Transaction
from .serializers import TransactionSerializer

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsManager] # Only managers can manage finances

    def get_queryset(self):
        return Transaction.objects.filter(farm=self.request.user.farm)

    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save(user=self.request.user, farm=self.request.user.farm)
