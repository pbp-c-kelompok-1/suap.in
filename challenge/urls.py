from django.urls import path
from . import views

app_name = 'challenge'

urlpatterns = [
    path('', views.challenge_list_view, name='list'),
    path('claim-freeze/', views.claim_freeze_view, name='claim_freeze'),
    path('report/', views.weekly_report_view, name='report'),
    path('api/daily/', views.api_daily_challenges, name='api_daily'),
    path('api/data/', views.api_challenge_data, name='api_data'),
]
