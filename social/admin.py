"""Pengaturan halaman admin Django (/admin/) untuk model-model modul Social.

@admin.register(Model) -> model itu muncul di halaman admin.
    list_display  : kolom yang tampil di tabel daftar
    list_filter   : filter di sisi kanan
    search_fields : kolom yang bisa dicari lewat kotak pencarian
    actions       : aksi massal untuk baris-baris yang dicentang
"""
from django.contrib import admin
from .models import Canteen, CampusMembership, CommunityPost, Friendship, PostReport, University


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


# Aksi moderasi: admin bisa menyembunyikan post yang tidak pantas tanpa menghapusnya.
# queryset = baris-baris yang dicentang admin. update() = 1 query UPDATE untuk semuanya.
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
    actions = [hide_posts, unhide_posts]   # muncul di dropdown "Action" halaman daftar post


@admin.register(PostReport)
class PostReportAdmin(admin.ModelAdmin):
    list_display = ['post', 'user', 'reason', 'created_at']


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'status', 'created_at', 'responded_at']
    list_filter = ['status']
    # from_user__username -> cari berdasarkan username pengirim (melewati relasi FK dengan "__").
    search_fields = ['from_user__username', 'to_user__username']
