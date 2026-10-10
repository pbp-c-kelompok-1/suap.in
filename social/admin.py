from django.contrib import admin
from .models import Canteen, CampusMembership, CommunityPost, PostReport, University


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ['short_name', 'name', 'city']
    search_fields = ['name', 'short_name']


@admin.register(CampusMembership)
class CampusMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'university', 'joined_at']
    list_filter = ['university']


@admin.register(Canteen)
class CanteenAdmin(admin.ModelAdmin):
    list_display = ['name', 'faculty', 'university', 'latitude', 'longitude', 'radius_m', 'is_active']
    list_filter = ['university', 'is_active']
    search_fields = ['name', 'faculty']


@admin.action(description='Sembunyikan post terpilih')
def hide_posts(modeladmin, request, queryset):
    queryset.update(is_hidden=True)


@admin.action(description='Tampilkan lagi post terpilih')
def unhide_posts(modeladmin, request, queryset):
    queryset.update(is_hidden=False)


@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
    list_display = ['user', 'food_name', 'canteen', 'price', 'total_co2_grams', 'is_shared', 'is_hidden', 'created_at']
    list_filter = ['is_shared', 'is_hidden', 'canteen']
    actions = [hide_posts, unhide_posts]


@admin.register(PostReport)
class PostReportAdmin(admin.ModelAdmin):
    list_display = ['post', 'user', 'reason', 'created_at']
