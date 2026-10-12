from django.db.models import Max
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .constants import SUPPORTED_CURRENCIES, CURRENCY_SYMBOLS
from .models import ExchangeRate
from .serializers import ExchangeRateSerializer


class CurrencyViewMixin:
    """View mixin that reads ?currency= and passes it to serializer context."""

    def get_serializer_context(self):
        context = super().get_serializer_context()
        currency = self.request.query_params.get('currency')
        if currency:
            valid_codes = [c[0] for c in SUPPORTED_CURRENCIES]
            if currency in valid_codes:
                context['display_currency'] = currency
        return context


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def supported_currencies(request):
    return Response({
        'currencies': [
            {'code': code, 'name': name, 'symbol': CURRENCY_SYMBOLS.get(code, code)}
            for code, name in SUPPORTED_CURRENCIES
        ],
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def latest_exchange_rates(request):
    latest_ids = (
        ExchangeRate.objects
        .values('base_currency', 'target_currency')
        .annotate(latest_id=Max('id'))
        .values_list('latest_id', flat=True)
    )
    rates = ExchangeRate.objects.filter(id__in=latest_ids)
    serializer = ExchangeRateSerializer(rates, many=True)
    return Response({'rates': serializer.data})
