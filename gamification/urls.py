from django.urls import path
from . import views

app_name = 'gamification'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('streak/', views.streak_view, name='streak'),
    path('level/', views.level_view, name='level'),
    path('badges/', views.badges_view, name='badges'),
    path('badges/api/', views.get_badge_json, name='get_badges_json'),
    path('badges/create/', views.create_badge_ajax, name='create_badge'),
    path('badges/<slug:code>/delete/', views.delete_badge, name='delete_badge')
]
