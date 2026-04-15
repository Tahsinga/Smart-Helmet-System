from rest_framework import serializers
from .models import SensorData

class SensorDataSerializer(serializers.ModelSerializer):
    humidity = serializers.FloatField(required=False, default=0.0)
    spo2 = serializers.FloatField(required=False, default=0.0)
    motion = serializers.FloatField(required=False, default=0.0)
    motion_x = serializers.FloatField(required=False, default=0.0)
    motion_y = serializers.FloatField(required=False, default=0.0)
    fall_detected = serializers.BooleanField(required=False, default=False)
    temperature = serializers.FloatField(required=False, default=0.0)
    gas_level = serializers.FloatField(required=False, default=0.0)
    heart_rate = serializers.IntegerField(required=False, default=0)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    
    class Meta:
        model = SensorData
        fields = ['helmet', 'heart_rate', 'spo2', 'gas_level', 'temperature', 'humidity', 'motion', 'motion_x', 'motion_y', 'fall_detected', 'latitude', 'longitude']
