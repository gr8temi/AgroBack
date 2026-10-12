from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta

from decimal import Decimal

from rest_framework import viewsets, permissions
from rest_framework.decorators import action, api_view, permission_classes as perm_classes
from rest_framework.response import Response

from core.idempotency import IdempotentCreateMixin
from core.permissions import IsManager, CanManageFinances
from currencies.utils import convert_amount
from currencies.views import CurrencyViewMixin

from .models import Transaction
from .serializers import TransactionSerializer


class TransactionViewSet(IdempotentCreateMixin, CurrencyViewMixin, viewsets.ModelViewSet):
    serializer_class = TransactionSerializer

    def get_permissions(self):
        if self.action == 'destroy':
            return [IsManager()]
        return [CanManageFinances()]

    def get_queryset(self):
        qs = Transaction.objects.filter(farm=self.request.user.farm)
        flock_id = self.request.query_params.get('related_flock')
        if flock_id:
            qs = qs.filter(related_flock_id=flock_id)
        return qs

    @transaction.atomic
    def perform_create(self, serializer):
        farm = self.request.user.farm
        input_currency = serializer.validated_data.get('currency') or farm.base_currency
        amount = serializer.validated_data['amount']
        save_kwargs = dict(user=self.request.user, farm=farm)
        if input_currency != farm.base_currency:
            save_kwargs.update(
                original_amount=amount,
                original_currency=input_currency,
                amount=convert_amount(amount, input_currency, farm.base_currency),
                currency=farm.base_currency,
            )
        else:
            save_kwargs.update(currency=farm.base_currency)
        instance = serializer.save(**save_kwargs)
        self._recalc_flock(instance.related_flock)

    @transaction.atomic
    def perform_update(self, serializer):
        old_flock_id = serializer.instance.related_flock_id
        instance = serializer.save()
        self._recalc_flock(instance.related_flock)
        if old_flock_id and old_flock_id != instance.related_flock_id:
            from flocks.models import Flock
            self._recalc_flock(Flock.objects.get(id=old_flock_id))

    @transaction.atomic
    def perform_destroy(self, instance):
        flock = instance.related_flock
        instance.delete()
        self._recalc_flock(flock)

    @staticmethod
    def _recalc_flock(flock):
        if flock:
            flock.compute_summary_stats()
            flock.save()

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """
        Get financial analytics for the farm.
        Query params:
        - period: number of days to analyze (default: 30)
        - currency: display currency code (default: farm's base currency)
        """
        try:
            period = max(int(request.query_params.get('period', 30)), 0)
        except (ValueError, TypeError):
            period = 30
        farm = request.user.farm
        display_currency = request.query_params.get('currency', farm.base_currency)

        end_date = timezone.now().date()
        transactions_qs = Transaction.objects.filter(farm=farm)
        if period > 0:
            start_date = end_date - timedelta(days=period)
            transactions_qs = transactions_qs.filter(
                date__gte=start_date,
                date__lte=end_date,
            )
        else:
            start_date = None
        flock_id = request.query_params.get('related_flock')
        if flock_id:
            transactions_qs = transactions_qs.filter(related_flock_id=flock_id)

        income_total = Decimal('0')
        expense_total = Decimal('0')
        expense_by_category = {}
        income_by_category = {}

        for t in transactions_qs:
            amount = convert_amount(t.amount, t.currency, display_currency)
            if t.type == 'expense':
                expense_total += amount
                expense_by_category[t.category] = expense_by_category.get(t.category, 0) + float(amount)
            else:
                income_total += amount
                income_by_category[t.category] = income_by_category.get(t.category, 0) + float(amount)

        top_expenses = sorted(expense_by_category.items(), key=lambda x: x[1], reverse=True)[:3]
        top_income = sorted(income_by_category.items(), key=lambda x: x[1], reverse=True)[:3]

        return Response({
            'period_days': period,
            'start_date': start_date,
            'end_date': end_date,
            'currency': display_currency,
            'total_income': float(income_total),
            'total_expenses': float(expense_total),
            'net_profit': float(income_total - expense_total),
            'expense_by_category': expense_by_category,
            'income_by_category': income_by_category,
            'top_expenses': [{'category': cat, 'amount': amt} for cat, amt in top_expenses],
            'top_income': [{'category': cat, 'amount': amt} for cat, amt in top_income],
        })


@api_view(['GET'])
@perm_classes([permissions.IsAuthenticated])
def finance_categories(request):
    categories = Transaction.CATEGORIES
    expense = []
    income = []
    for key, label in categories:
        entry = {'key': key, 'label': label}
        if key in ('egg_sales', 'bird_sales', 'manure_sales'):
            income.append(entry)
        elif key == 'other':
            expense.append(entry)
            income.append(entry)
        else:
            expense.append(entry)
    return Response({'expense': expense, 'income': income})

