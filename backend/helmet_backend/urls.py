from django.contrib import admin
from django.urls import path, include
from monitoring.views import (
    dashboard_view, WorkerLoginView, AdminLoginView, create_user_view, logout_view
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('monitoring.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('worker-login/', WorkerLoginView.as_view(), name='worker_login'),
    path('admin-login/', AdminLoginView.as_view(), name='admin_login'),
    path('logout/', logout_view, name='logout'),
    path('create-user/', create_user_view, name='create_user'),
    path('', WorkerLoginView.as_view(), name='home'),
]
