from django.urls import path
from . import views

app_name = 'gamification'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('streak/', views.streak_view, name='streak'),
    path('level/', views.level_view, name='level'),
    path('story/', views.story_view, name='story'),
]
