from django.urls import path
from . import views

app_name = 'social'

urlpatterns = [
    path('', views.leaderboard_view, name='leaderboard'),
    path('friends/', views.friends_view, name='friends'),
    path('campus-war/', views.campus_war_view, name='campus_war'),
    path('challenge/<int:pk>/', views.challenge_view, name='challenge'),
]
