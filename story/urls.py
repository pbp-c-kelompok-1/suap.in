from django.urls import path
from . import views, reward_views

app_name = 'story'

urlpatterns = [
    path('rewards/', reward_views.reward_list, name='reward_list'),
    path('rewards/<int:pk>/claim/', reward_views.reward_claim, name='reward_claim'),
    path('manage/', views.story_manage, name='manage'),
    path('manage/comics/new/', views.comic_edit, name='comic_create'),
    path('manage/comics/<uuid:pk>/edit/', views.comic_edit, name='comic_edit'),
    path('manage/comics/<uuid:pk>/delete/', views.comic_delete, name='comic_delete'),
    path('manage/comics/<uuid:comic_pk>/pages/new/', views.page_edit, name='page_create'),
    path('manage/comics/<uuid:comic_pk>/pages/<int:pk>/edit/', views.page_edit, name='page_edit'),
    path('manage/comics/<uuid:comic_pk>/pages/<int:pk>/delete/', views.page_delete, name='page_delete'),
    path('', views.story_list, name='story_list'),
    path('<int:bab>/', views.story_reader, name='story_reader'),
    path('challenges/', views.challenge_list, name='challenge_list'),
    path('challenges/<uuid:pk>/cancel/', views.cancel_challenge, name='cancel_challenge'),
    path('challenges/<uuid:pk>/accept/', views.challenge_accept, name='challenge_accept'),
    path('challenges/<uuid:pk>/refresh/', views.challenge_refresh, name='challenge_refresh'),
]
