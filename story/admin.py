from django.contrib import admin

from .models import FriendChallenge, StoryComic, StoryPage


@admin.register(StoryComic)
class StoryComicAdmin(admin.ModelAdmin):
    list_display = ['bab', 'title', 'unlock_level', 'total_pages', 'is_published']
    list_filter = ['is_published']
    search_fields = ['title', 'description']


@admin.register(FriendChallenge)
class FriendChallengeAdmin(admin.ModelAdmin):
    list_display = ['challenger', 'opponent', 'metric', 'duration_days', 'status', 'created_at']
    list_filter = ['status', 'metric']


@admin.register(StoryPage)
class StoryPageAdmin(admin.ModelAdmin):
    list_display = ['comic', 'position', 'title', 'scene']
    list_filter = ['comic', 'scene']
    search_fields = ['title', 'narration']
