"""URL modul Social = "daftar alamat" -> view mana yang menangani.

File ini di-include dari urls.py utama project dengan awalan /social/,
jadi path('friends/', ...) di sini berarti alamat lengkapnya /social/friends/.

name='...' dipakai untuk memanggil URL tanpa menulis alamat manual:
    di Python  : reverse('social:friends') / redirect('social:friends')
    di template: {% url 'social:friends' %}
<int:pk> = bagian URL berupa angka yang dikirim ke view sebagai parameter `pk`.
"""
from django.urls import path
from django.views.generic import RedirectView
from . import api_views, views

# Namespace -> nama URL ditulis 'social:xxx' supaya tidak bentrok dengan app lain.
app_name = 'social'

urlpatterns = [
    # /social/ langsung dialihkan ke halaman leaderboard.
    path('', RedirectView.as_view(pattern_name='social:leaderboard'), name='index'),

    # --- Leaderboard & Campus War ---
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),            # GET  ?tab=&partial=
    path('campus-war/', views.campus_war_view, name='campus_war'),               # GET
    path('campus/choose/', views.choose_campus_view, name='choose_campus'),      # GET form / POST simpan

    # --- Community (peta) --- halaman + 3 API JSON yang dipanggil JavaScript peta
    path('community/', views.community_map_view, name='community_map'),
    path('community/api/canteens/', views.api_canteens, name='api_canteens'),                         # GET pin
    path('community/api/canteens/<int:pk>/posts/', views.api_canteen_posts, name='api_canteen_posts'),  # GET panel
    path('community/api/nearest/', views.api_nearest, name='api_nearest'),                            # POST lat/lng

    # --- Teman (CRUD Friendship) ---
    path('friends/', views.friends_view, name='friends'),                                         # Read
    path('friends/request/', views.friend_request_send, name='friend_request_send'),              # Create (POST)
    path('friends/<int:pk>/respond/', views.friend_request_respond, name='friend_request_respond'),  # Update (POST)
    path('friends/<int:pk>/delete/', views.friendship_delete, name='friendship_delete'),          # Delete (POST)

    # Placeholder tantangan 1v1
    path('challenge/<int:pk>/', views.challenge_view, name='challenge'),

    # --- API JSON (Django REST Framework) untuk aplikasi mobile Flutter --- lihat api_views.py
    path('api/leaderboard/', api_views.api_leaderboard, name='api_leaderboard'),                 # GET ?tab=
    path('api/campus-war/', api_views.api_campus_war, name='api_campus_war'),                    # GET
    path('api/universities/', api_views.api_universities, name='api_universities'),              # GET
    path('api/campus/', api_views.api_choose_campus, name='api_choose_campus'),                  # POST
    path('api/friends/', api_views.api_friends, name='api_friends'),                             # GET ?q=
    path('api/friends/request/', api_views.api_friend_request, name='api_friend_request'),       # POST
    path('api/friends/<int:pk>/respond/', api_views.api_friend_respond, name='api_friend_respond'),  # POST
    path('api/friends/<int:pk>/delete/', api_views.api_friend_delete, name='api_friend_delete'),     # POST
]
