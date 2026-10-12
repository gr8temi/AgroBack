from datetime import date
from decimal import Decimal

from rest_framework import serializers

from currencies.serializers import CurrencyConversionMixin

from .models import Flock, FeedLog, HealthLog, EggCollection


class FlockSerializer(CurrencyConversionMixin, serializers.ModelSerializer):
    currency_fields = ['total_feed_cost', 'total_health_cost', 'total_income', 'total_expense']
    currency_source_field = 'currency'

    cycle_duration_days = serializers.SerializerMethodField()
    net_profit = serializers.SerializerMethodField()

    class Meta:
        model = Flock
        fields = '__all__'
        read_only_fields = (
            'user', 'farm',
            'total_eggs_collected', 'total_feed_kg', 'total_feed_cost',
            'total_health_cost', 'total_mortality',
            'total_income', 'total_expense',
        )

    def get_cycle_duration_days(self, obj):
        if obj.start_date:
            end = obj.end_date or date.today()
            return (end - obj.start_date).days
        return None

    def get_net_profit(self, obj):
        return float(obj.total_income - obj.total_expense)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if 'total_income' in data and 'total_expense' in data:
            data['net_profit'] = float(
                Decimal(str(data['total_income'])) - Decimal(str(data['total_expense']))
            )
        return data


class FlockCloseSerializer(serializers.Serializer):
    closure_reason = serializers.ChoiceField(choices=Flock.CLOSURE_REASON_CHOICES)
    closure_notes = serializers.CharField(required=False, allow_blank=True, default='')
    end_date = serializers.DateField(required=False)


class FlockOwnedMixin:
    """Validates that the referenced flock belongs to the requesting user's farm."""
    def validate_flock(self, value):
        request = self.context.get("request")
        if request and value.farm_id != request.user.farm_id:
            raise serializers.ValidationError("Flock does not belong to your farm.")
        if value.status == 'closed':
            raise serializers.ValidationError("Cannot add logs to a closed cycle.")
        return value


class FeedLogSerializer(CurrencyConversionMixin, FlockOwnedMixin, serializers.ModelSerializer):
    currency_fields = ['cost']
    currency_source_field = 'currency'

    class Meta:
        model = FeedLog
        fields = '__all__'


class HealthLogSerializer(CurrencyConversionMixin, FlockOwnedMixin, serializers.ModelSerializer):
    currency_fields = ['cost']
    currency_source_field = 'currency'

    class Meta:
        model = HealthLog
        fields = '__all__'


class EggCollectionSerializer(FlockOwnedMixin, serializers.ModelSerializer):
    class Meta:
        model = EggCollection
        fields = '__all__'
