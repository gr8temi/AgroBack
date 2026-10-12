from rest_framework import serializers

from core.idempotency import ClientIdSerializerMixin
from currencies.serializers import CurrencyConversionMixin

from .models import Transaction


class TransactionSerializer(CurrencyConversionMixin, ClientIdSerializerMixin, serializers.ModelSerializer):
    currency_fields = ['amount']
    currency_source_field = 'currency'

    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ('user', 'farm')

    def validate_related_flock(self, value):
        if value is None:
            return value
        request = self.context.get("request")
        if request and value.farm_id != request.user.farm_id:
            raise serializers.ValidationError("Flock does not belong to your farm.")
        if value.status == 'closed':
            raise serializers.ValidationError("Cannot add transactions to a closed cycle.")
        return value
