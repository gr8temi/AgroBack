from django.db import transaction as db_transaction
from django.utils import timezone

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from core.permissions import CanManageFinances
from finances.models import Transaction

from .models import Invoice
from .serializers import InvoiceSerializer


class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer

    def get_permissions(self):
        return [CanManageFinances()]

    def get_queryset(self):
        qs = Invoice.objects.filter(
            farm=self.request.user.farm,
        ).prefetch_related('line_items')

        flock_id = self.request.query_params.get('related_flock')
        if flock_id:
            qs = qs.filter(related_flock_id=flock_id)

        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)

        date_from = self.request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(invoice_date__gte=date_from)

        date_to = self.request.query_params.get('date_to')
        if date_to:
            qs = qs.filter(invoice_date__lte=date_to)

        return qs

    @db_transaction.atomic
    def perform_create(self, serializer):
        serializer.save()

    @db_transaction.atomic
    def perform_update(self, serializer):
        if serializer.instance.status in ('paid', 'cancelled'):
            raise PermissionDenied("Cannot modify a paid or cancelled invoice.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.status in ('paid', 'cancelled'):
            raise PermissionDenied("Cannot delete a paid or cancelled invoice.")
        instance.delete()

    @action(detail=True, methods=['post'])
    def mark_sent(self, request, pk=None):
        invoice = self.get_object()
        if invoice.status != 'draft':
            return Response(
                {'detail': 'Only draft invoices can be marked as sent.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        invoice.status = 'sent'
        invoice.save(update_fields=['status', 'updated_at'])
        return Response(InvoiceSerializer(invoice).data)

    @db_transaction.atomic
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        invoice = self.get_object()
        if invoice.status != 'sent':
            return Response(
                {'detail': 'Only sent invoices can be marked as paid.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        invoice.status = 'paid'
        invoice.save(update_fields=['status', 'updated_at'])

        tx = Transaction.objects.create(
            user=request.user,
            farm=invoice.farm,
            date=timezone.now().date(),
            type='income',
            category=invoice.category,
            amount=invoice.grand_total,
            currency=invoice.farm.base_currency,
            description=f"Payment for {invoice.invoice_number} - {invoice.customer_name}",
            related_flock=invoice.related_flock,
            invoice=invoice,
        )

        if tx.related_flock:
            tx.related_flock.compute_summary_stats()
            tx.related_flock.save()

        return Response(InvoiceSerializer(invoice).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        invoice = self.get_object()
        if invoice.status in ('paid', 'cancelled'):
            return Response(
                {'detail': f'Cannot cancel a {invoice.status} invoice.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        invoice.status = 'cancelled'
        invoice.save(update_fields=['status', 'updated_at'])
        return Response(InvoiceSerializer(invoice).data)
