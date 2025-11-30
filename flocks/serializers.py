from rest_framework import serializers
from .models import Flock, FeedLog, HealthLog, EggCollection

class FlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flock
        fields = '__all__'
        read_only_fields = ('user',)

class FeedLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedLog
        fields = '__all__'

class HealthLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthLog
        fields = '__all__'

class EggCollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EggCollection
        fields = '__all__'
