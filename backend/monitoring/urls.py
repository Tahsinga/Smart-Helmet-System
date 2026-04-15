from django.urls import path
from .views import (
    receive_sensor_data, dashboard_view, dashboard_map_view, dashboard_live, dashboard_ai_analyze, dashboard_history, resolve_alert,
    workers_list_view, worker_history_view, worker_history_data
)

urlpatterns = [
    path("sensor-data/", receive_sensor_data),

    path("dashboard/", dashboard_view, name="dashboard"),
    path("dashboard/map/", dashboard_map_view, name="dashboard_map"),
    path("dashboard/live/", dashboard_live, name="dashboard_live"),
    path("dashboard/analyze/", dashboard_ai_analyze, name="dashboard_ai_analyze"),
    path("dashboard/history/", dashboard_history, name="dashboard_history"),

    path("alerts/<int:alert_id>/resolve/", resolve_alert),

    # ✅ Worker History pages + data
    path("workers/", workers_list_view),
    path("workers/<str:device_id>/", worker_history_view),
    path("workers/<str:device_id>/history/", worker_history_data),
]
