from django.urls import path
from . import views

app_name = 'scanner'

urlpatterns = [
    path('', views.scan_view, name='scan'),
    path('result/', views.result_view, name='result'),
    path('save/', views.save_log_view, name='save_log'),
    path('log/', views.daily_log_view, name='daily_log'),
    path('log/delete/<int:log_id>/', views.delete_log_view, name='delete_log'),
    path('api/status/', views.api_scan_status, name='api_status'),
]
