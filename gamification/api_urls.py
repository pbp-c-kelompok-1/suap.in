from django.urls import path
from gamification import api_views

app_name = "api"
urlpatterns = [
    path("badges/", api_views.badge_list, name="badges-list"),
    path("badges/<slug:code>/", api_views.badge_detail, name="badge-detail"),
    path("user/badges/", api_views.user_badges_list, name="user-badges"),
    path("user/game_profile", api_views.user_game_profile, name="user-game-profile")
]