from decimal import Decimal

from rest_framework import serializers

from .models import ExchangeRate
from .utils import convert_amount


class ExchangeRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRate
        fields = ('base_currency', 'target_currency', 'rate', 'fetched_at')


class CurrencyConversionMixin:
    """
    Serializer mixin that converts monetary fields to a display currency.

    Subclasses set:
        currency_fields = ['amount']           # fields to convert
        currency_source_field = 'currency'     # field holding the record's currency code

    Views pass 'display_currency' in the serializer context via CurrencyViewMixin.
    """
    currency_fields = []
    currency_source_field = 'currency'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        display_currency = self.context.get('display_currency')
        if not display_currency:
            return data

        source_currency = getattr(instance, self.currency_source_field, None)
        if not source_currency or source_currency == display_currency:
            return data

        try:
            for field in self.currency_fields:
                value = data.get(field)
                if value is not None:
                    data[field] = str(convert_amount(
                        Decimal(str(value)), source_currency, display_currency
                    ))
            data['display_currency'] = display_currency
            data['original_currency'] = source_currency
        except ValueError:
            pass

        return data
