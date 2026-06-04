from rest_framework import serializers
from .models import Flock, FeedLog, HealthLog, EggCollection

class FlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flock
        fields = '__all__'
        read_only_fields = ('user', 'farm')


class FlockOwnedMixin:
    """Validates that the referenced flock belongs to the requesting user's farm."""
    def validate_flock(self, value):
        request = self.context.get("request")
        if request and value.farm_id != request.user.farm_id:
            raise serializers.ValidationError("Flock does not belong to your farm.")
        return value


class FeedLogSerializer(FlockOwnedMixin, serializers.ModelSerializer):
    class Meta:
        model = FeedLog
        fields = '__all__'


class HealthLogSerializer(FlockOwnedMixin, serializers.ModelSerializer):
    class Meta:
        model = HealthLog
        fields = '__all__'


class EggCollectionSerializer(FlockOwnedMixin, serializers.ModelSerializer):
    class Meta:
        model = EggCollection
        fields = '__all__'
