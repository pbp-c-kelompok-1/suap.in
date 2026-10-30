import sys

from django.db import migrations
from django.utils import timezone

from social.seed import SEED_SCAN_PREFIX, seed_leaderboard_scans

# Riwayat scan makanan untuk akun contoh leaderboard. Semua peringkat (Peringkat,
# Laporan mingguan, Campus War) dihitung dari emisi CO2 per scan, jadi tanpa ini
# akun contoh tidak akan muncul di peringkat mana pun.


def seed(apps, schema_editor):
    if 'test' in sys.argv:
        return  # database test harus kosong; data showcase hanya untuk server/laptop
    seed_leaderboard_scans(apps.get_model('auth', 'User'), apps.get_model('scanner', 'FoodLog'), timezone.localtime())


def unseed(apps, schema_editor):
    apps.get_model('scanner', 'FoodLog').objects.filter(ai_raw_response__startswith=SEED_SCAN_PREFIX).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('scanner', '0001_initial'),
        ('social', '0008_delete_xpactivity'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
