from django.contrib import admin
from .models import Badge, GameProfile, UserBadge
 
 
@admin.register(GameProfile)
class GameProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'level', 'total_xp', 'current_streak', 'record_streak', 'streak_freezes']
    search_fields = ['user__username']
 
 
@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'criteria_type', 'threshold']
    list_filter = ['criteria_type']
 
 
@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ['user', 'badge', 'earned_at']
    list_filter = ['badge']
 