"""Perintah terminal: python manage.py seed_community

Mengisi peta Community dengan foto contoh supaya peta tidak kosong saat demo.
Nama file (seed_community.py) = nama perintahnya. Django mencari class bernama `Command`.
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from social.models import Canteen, CommunityPost, University
from social.seed import ensure_canteens, seed_community_posts


class Command(BaseCommand):
    # Teks bantuan yang muncul di: python manage.py help seed_community
    help = 'Isi peta Community dengan foto showcase dari social/seed/community_seed.json'

    def handle(self, *args, **options):
        """Dijalankan saat perintah dipanggil. self.stdout.write = print ke terminal."""
        ensure_canteens(University, Canteen, log=self.stdout.write)          # 1. pastikan kampus & kantin ada
        seed_community_posts(User, Canteen, CommunityPost, log=self.stdout.write, verbose=True)  # 2. buat post
