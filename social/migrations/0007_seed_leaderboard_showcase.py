import sys

from django.db import migrations
from django.utils import timezone

from social.seed import ensure_canteens, seed_leaderboard_profiles, unseed_leaderboard

# Akun contoh + XP/level + kampus. Riwayat scan-nya (dasar peringkat CO2)
# dibuat di 0009_seed_leaderboard_scans.


def models(apps):
    return (apps.get_model('auth', 'User'), apps.get_model('social', 'CampusMembership'),
            apps.get_model('gamification', 'GameProfile'))


def seed(apps, schema_editor):
    if 'test' in sys.argv:
        return  # database test harus kosong; data showcase hanya untuk server/laptop
    University = apps.get_model('social', 'University')
    ensure_canteens(University, apps.get_model('social', 'Canteen'))
    User, CampusMembership, GameProfile = models(apps)
    seed_leaderboard_profiles(User, University, CampusMembership, GameProfile, timezone.localtime())


def unseed(apps, schema_editor):
    unseed_leaderboard(*models(apps))


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('gamification', '0002_gameprofile_freeze_week_start_and_more'),
        ('social', '0006_xpactivity'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
