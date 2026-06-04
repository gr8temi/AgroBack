from datetime import date

from django.db import transaction

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from core.permissions import IsManager, IsStaff

from .models import Flock, FeedLog, HealthLog, EggCollection
from .serializers import (
    FlockSerializer,
    FlockCloseSerializer,
    FeedLogSerializer,
    HealthLogSerializer,
    EggCollectionSerializer,
)


class FlockViewSet(viewsets.ModelViewSet):
    serializer_class = FlockSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'cycle_comparison']:
            permission_classes = [IsStaff]
        else:
            permission_classes = [IsManager]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        qs = Flock.objects.filter(farm=self.request.user.farm)
        status_filter = self.request.query_params.get('status')
        if status_filter in ('active', 'closed'):
            qs = qs.filter(status=status_filter)
        return qs.order_by('-date_added')

    @transaction.atomic
    def perform_create(self, serializer):
        start = serializer.validated_data.get('start_date') or date.today()
        serializer.save(
            user=self.request.user,
            farm=self.request.user.farm,
            start_date=start,
            status='active',
        )

    def perform_update(self, serializer):
        if serializer.instance.status == 'closed':
            raise PermissionDenied("Cannot modify a closed cycle.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.status == 'closed':
            raise PermissionDenied("Cannot delete a closed cycle.")
        instance.delete()

    @transaction.atomic
    @action(detail=True, methods=['post'], permission_classes=[IsManager])
    def close_cycle(self, request, pk=None):
        flock = self.get_object()
        if flock.status == 'closed':
            return Response(
                {'detail': 'Cycle is already closed.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = FlockCloseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        flock.status = 'closed'
        flock.closure_reason = serializer.validated_data['closure_reason']
        flock.closure_notes = serializer.validated_data.get('closure_notes', '')
        flock.end_date = serializer.validated_data.get('end_date') or date.today()
        flock.compute_summary_stats()
        flock.save()

        return Response(FlockSerializer(flock).data)

    @transaction.atomic
    @action(detail=True, methods=['post'], permission_classes=[IsManager])
    def reopen_cycle(self, request, pk=None):
        flock = self.get_object()
        if flock.status != 'closed':
            return Response(
                {'detail': 'Cycle is not closed.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        flock.status = 'active'
        flock.end_date = None
        flock.closure_reason = None
        flock.closure_notes = ''
        flock.save()

        return Response(FlockSerializer(flock).data)

    @action(detail=False, methods=['get'], permission_classes=[IsStaff])
    def cycle_comparison(self, request):
        qs = Flock.objects.filter(farm=request.user.farm)

        status_filter = request.query_params.get('status')
        if status_filter in ('active', 'closed'):
            qs = qs.filter(status=status_filter)

        flock_ids = request.query_params.get('flock_ids')
        if flock_ids:
            ids = [int(x) for x in flock_ids.split(',') if x.strip().isdigit()]
            qs = qs.filter(id__in=ids)

        cycles = []
        for flock in qs.order_by('-start_date'):
            duration = None
            if flock.start_date:
                end = flock.end_date or date.today()
                duration = (end - flock.start_date).days

            cycles.append({
                'id': flock.id,
                'name': flock.name,
                'breed': flock.breed,
                'status': flock.status,
                'start_date': flock.start_date,
                'end_date': flock.end_date,
                'duration_days': duration,
                'initial_quantity': flock.initial_quantity,
                'final_quantity': flock.current_quantity,
                'mortality': flock.total_mortality,
                'mortality_rate': round(
                    flock.total_mortality / flock.initial_quantity * 100, 2
                ) if flock.initial_quantity > 0 else 0,
                'total_eggs': flock.total_eggs_collected,
                'eggs_per_bird': round(
                    flock.total_eggs_collected / flock.initial_quantity, 1
                ) if flock.initial_quantity > 0 else 0,
                'total_feed_kg': float(flock.total_feed_kg),
                'total_feed_cost': float(flock.total_feed_cost),
                'total_health_cost': float(flock.total_health_cost),
                'total_income': float(flock.total_income),
                'total_expense': float(flock.total_expense),
                'net_profit': float(flock.total_income - flock.total_expense),
                'roi': round(
                    float(flock.total_income - flock.total_expense)
                    / float(flock.total_expense) * 100, 2
                ) if flock.total_expense > 0 else None,
                'closure_reason': flock.closure_reason,
            })

        return Response({'count': len(cycles), 'cycles': cycles})


class FeedLogViewSet(viewsets.ModelViewSet):
    serializer_class = FeedLogSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        return FeedLog.objects.filter(flock__farm=self.request.user.farm)


class HealthLogViewSet(viewsets.ModelViewSet):
    serializer_class = HealthLogSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        return HealthLog.objects.filter(flock__farm=self.request.user.farm)


class EggCollectionViewSet(viewsets.ModelViewSet):
    serializer_class = EggCollectionSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        return EggCollection.objects.filter(flock__farm=self.request.user.farm)
