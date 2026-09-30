from django.urls import path
from . import views

app_name = 'story'

urlpatterns = [
    path('', views.story_list, name='story_list'),
    path('<int:bab>/', views.story_reader, name='story_reader'),
    path('milestones/', views.milestone_list, name='milestone_list'),
    path('milestones/<uuid:pk>/claim/', views.claim_milestone, name='claim_milestone'),
    path('challenges/', views.challenge_list, name='challenge_list'),
    path('challenges/<uuid:pk>/cancel/', views.cancel_challenge, name='cancel_challenge'),
]
