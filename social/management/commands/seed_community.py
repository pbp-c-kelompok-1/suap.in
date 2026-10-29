from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from social.models import Canteen, CommunityPost, University
from social.seed import ensure_canteens, seed_community_posts


class Command(BaseCommand):
    help = 'Isi peta Community dengan foto showcase dari social/seed/community_seed.json'

    def handle(self, *args, **options):
        ensure_canteens(University, Canteen, log=self.stdout.write)
        seed_community_posts(User, Canteen, CommunityPost, log=self.stdout.write, verbose=True)
