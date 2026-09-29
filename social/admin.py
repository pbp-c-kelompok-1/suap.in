from django.contrib import admin
from .models import CampusMembership, University


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ['short_name', 'name', 'city']
    search_fields = ['name', 'short_name']


@admin.register(CampusMembership)
class CampusMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'university', 'joined_at']
    list_filter = ['university']
