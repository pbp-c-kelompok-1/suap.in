from django.urls import path
from . import views

app_name = 'story'

urlpatterns = [
    path('', views.story_list, name='story_list'),
    path('<int:bab>/', views.story_reader, name='story_reader'),
    path('challenges/', views.challenge_list, name='challenge_list'),
    path('challenges/<uuid:pk>/cancel/', views.cancel_challenge, name='cancel_challenge'),
]
