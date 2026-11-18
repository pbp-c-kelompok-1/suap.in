"""Perintah terminal: python manage.py seed_leaderboard [--friends-of USERNAME]

Mengisi leaderboard dengan akun contoh + riwayat scan supaya peringkat ramai saat demo.
Contoh: python manage.py seed_leaderboard --friends-of iqbal
        -> akun contoh juga dijadikan teman 'iqbal' supaya tab Teman terisi.
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from gamification.models import GameProfile
from scanner.models import FoodLog
from social.models import CampusMembership, Canteen, Friendship, University
from social.seed import ensure_canteens, load_leaderboard_entries, seed_leaderboard

# Akun contoh yang dijadikan teman saat memakai --friends-of.
DEMO_FRIENDS = ['zahra.aulia', 'rizky.ramadhan', 'nabila.khairunnisa', 'dimas.prasetyo', 'sekar.ayuningtyas']


class Command(BaseCommand):
    help = ('Isi leaderboard dengan akun contoh (kampus, XP, dan riwayat scan makanan). '
            'Jalankan lagi sebelum demo supaya peringkat mingguan & Campus War tetap ramai.')

    def add_arguments(self, parser):
        """Daftarkan opsi tambahan perintah. --friends-of masuk ke options['friends_of']."""
        parser.add_argument('--friends-of', metavar='USERNAME',
                            help='jadikan beberapa akun contoh teman USERNAME (untuk demo tab Teman)')

    def handle(self, *args, **options):
        # 1. Kampus & kantin, lalu akun contoh + profil game + riwayat scan.
        ensure_canteens(University, Canteen, log=self.stdout.write)
        seed_leaderboard(User, University, CampusMembership, GameProfile, FoodLog, timezone.localtime(),
                         log=self.stdout.write)

        # 2. Opsional: jadikan akun contoh teman user tertentu.
        username = options.get('friends_of')
        if not username:
            return
        me = User.objects.filter(username=username).first()
        if me is None:
            # CommandError -> pesan merah di terminal dan perintah berhenti.
            raise CommandError(f'User "{username}" tidak ditemukan.')
        seeded = {e['username'] for e in load_leaderboard_entries()}
        # password='!' -> hanya akun contoh (bukan akun asli dengan nama sama).
        for friend in User.objects.filter(username__in=[u for u in DEMO_FRIENDS if u in seeded], password='!'):
            accepted = {'status': Friendship.ACCEPTED, 'responded_at': timezone.now()}
            # Kalau akun contoh sudah pernah mengirim permintaan ke aku -> ubah jadi ACCEPTED.
            # update() return 0 kalau tidak ada baris -> buat/ubah baris dari arah aku -> dia.
            if not Friendship.objects.filter(from_user=friend, to_user=me).update(**accepted):
                Friendship.objects.update_or_create(from_user=me, to_user=friend, defaults=accepted)
        self.stdout.write(f'  {username} sekarang berteman dengan {", ".join(DEMO_FRIENDS)}.')
