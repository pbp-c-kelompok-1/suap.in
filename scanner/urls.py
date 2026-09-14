from django.urls import path
from . import views

app_name = 'scanner'

urlpatterns = [
    path('', views.scan_view, name='scan'),
    path('log/', views.daily_log_view, name='daily_log'),
    path('api/scan/', views.api_scan, name='api_scan'),
]
