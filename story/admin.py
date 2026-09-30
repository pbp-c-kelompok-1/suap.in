from django.contrib import admin

from .models import FriendChallenge, MilestoneReward, StoryComic


@admin.register(StoryComic)
class StoryComicAdmin(admin.ModelAdmin):
    list_display = ['bab', 'title', 'unlock_level', 'total_pages']


@admin.register(MilestoneReward)
class MilestoneRewardAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'days_required', 'is_claimed', 'claimed_at']
    list_filter = ['is_claimed']


@admin.register(FriendChallenge)
class FriendChallengeAdmin(admin.ModelAdmin):
    list_display = ['challenger', 'opponent', 'metric', 'duration_days', 'status', 'created_at']
    list_filter = ['status', 'metric']
