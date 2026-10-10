from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'social'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='social:leaderboard'), name='index'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('campus-war/', views.campus_war_view, name='campus_war'),
    path('campus/choose/', views.choose_campus_view, name='choose_campus'),
    path('community/', views.community_map_view, name='community_map'),
    path('community/api/canteens/', views.api_canteens, name='api_canteens'),
    path('community/api/canteens/<int:pk>/posts/', views.api_canteen_posts, name='api_canteen_posts'),
    path('community/api/nearest/', views.api_nearest, name='api_nearest'),
    path('friends/', views.friends_view, name='friends'),
    path('challenge/<int:pk>/', views.challenge_view, name='challenge'),
]
