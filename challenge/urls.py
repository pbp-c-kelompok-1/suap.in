from django.urls import path
from . import views

app_name = 'challenge'

urlpatterns = [
    path('', views.challenge_list_view, name='list'),
    path('claim-freeze/', views.claim_freeze_view, name='claim_freeze'),
    path('claim-quest/', views.claim_quest_view, name='claim_quest'),
    path('notifications/read/', views.notifications_read_view, name='notif_read'),
    path('notifications/dismiss/', views.notification_dismiss_view, name='notif_dismiss'),
    path('report/', views.weekly_report_view, name='report'),
    path('api/daily/', views.api_daily_challenges, name='api_daily'),
    path('api/data/', views.api_challenge_data, name='api_data'),
    path('api/stats/', views.api_stats_view, name='api_stats'),
    path('profile/save/', views.save_profile_view, name='save_profile'),
]
