from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

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

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """
        Get financial analytics for the farm
        Query params:
        - period: number of days to analyze (default: 30)
        """
        period = int(request.query_params.get('period', 30))
        farm = request.user.farm
        
        # Calculate date range
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=period)
        
        # Get transactions in period
        transactions = Transaction.objects.filter(
            farm=farm,
            date__gte=start_date,
            date__lte=end_date
        )
        
        # Calculate totals
        income_total = transactions.filter(type='income').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        expense_total = transactions.filter(type='expense').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Category breakdown
        expense_by_category = {}
        income_by_category = {}
        
        for t in transactions:
            if t.type == 'expense':
                expense_by_category[t.category] = expense_by_category.get(t.category, 0) + float(t.amount)
            else:
                income_by_category[t.category] = income_by_category.get(t.category, 0) + float(t.amount)
        
        # Top categories
        top_expenses = sorted(expense_by_category.items(), key=lambda x: x[1], reverse=True)[:3]
        top_income = sorted(income_by_category.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return Response({
            'period_days': period,
            'start_date': start_date,
            'end_date': end_date,
            'total_income': float(income_total),
            'total_expenses': float(expense_total),
            'net_profit': float(income_total - expense_total),
            'expense_by_category': expense_by_category,
            'income_by_category': income_by_category,
            'top_expenses': [{'category': cat, 'amount': amt} for cat, amt in top_expenses],
            'top_income': [{'category': cat, 'amount': amt} for cat, amt in top_income],
        })

