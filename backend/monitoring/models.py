from django.db import models
from django.contrib.auth.models import User

# Worker model
class Worker(models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='worker_profile')
    name = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# Helmet Device model
class HelmetDevice(models.Model):
    device_id = models.CharField(max_length=100, unique=True)
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, null=True, blank=True)
    battery_level = models.IntegerField(default=100)

    def __str__(self):
        return f"Helmet {self.device_id}"


# Sensor Data model
class SensorData(models.Model):
    helmet = models.ForeignKey(HelmetDevice, on_delete=models.CASCADE)
    heart_rate = models.IntegerField()
    spo2 = models.FloatField(null=True, blank=True, default=0)  # SpO2 from MAX30102 sensor
    gas_level = models.FloatField()
    temperature = models.FloatField()
    humidity = models.FloatField()
    motion = models.FloatField(null=True, blank=True, default=0.0)
    motion_x = models.FloatField(null=True, blank=True, default=0.0)
    motion_y = models.FloatField(null=True, blank=True, default=0.0)
    fall_detected = models.BooleanField(default=False)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)


# Alert model
class Alert(models.Model):
    ALERT_TYPES = [
        ('GAS', 'Hazardous Gas'),
        ('FALL', 'Fall Detected'),
        ('FATIGUE', 'Fatigue Detected'),
        ('HEART', 'Abnormal Heart Rate'),
    ]

    helmet = models.ForeignKey(HelmetDevice, on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.alert_type} Alert - {self.helmet.device_id}"
