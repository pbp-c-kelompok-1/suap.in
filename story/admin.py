from django.contrib import admin

from .models import FriendChallenge, StoryComic


@admin.register(StoryComic)
class StoryComicAdmin(admin.ModelAdmin):
    list_display = ['bab', 'title', 'unlock_level', 'total_pages']


@admin.register(FriendChallenge)
class FriendChallengeAdmin(admin.ModelAdmin):
    list_display = ['challenger', 'opponent', 'metric', 'duration_days', 'status', 'created_at']
    list_filter = ['status', 'metric']
