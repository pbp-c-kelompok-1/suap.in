from django.urls import path
from . import views

app_name = 'challenge'

urlpatterns = [
    path('', views.challenge_list_view, name='list'),
    path('report/', views.weekly_report_view, name='report'),
    path('api/daily/', views.api_daily_challenges, name='api_daily'),
]
