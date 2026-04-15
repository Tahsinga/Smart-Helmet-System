from django.contrib import admin
from .models import Worker, HelmetDevice, SensorData, Alert

admin.site.register(Worker)
admin.site.register(HelmetDevice)
admin.site.register(SensorData)
admin.site.register(Alert)
