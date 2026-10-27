from django.test import TestCase
from django.contrib.auth.models import User

from gamification.models import *
from scanner.models import FoodLog

from . import services


def make_logs(user, count):
    for i in range(count):
        FoodLog.objects.create(user=user, custom_name=f'Item {i}', co2_grams=100)


class LevelCalculationTests(TestCase):
    def test_xp_needed(self):
        self.assertEqual(services.xp_needed(1), 60)
        self.assertEqual(services.xp_needed(5), 100)

    def test_xp_floor(self):
        self.assertEqual(services.xp_floor(1), 0)
        self.assertEqual(services.xp_floor(2), 60)
        self.assertEqual(services.xp_floor(3), 130)

    def test_level_from_xp(self):
        self.assertEqual(services.level_from_xp(0), 1)
        self.assertEqual(services.level_from_xp(59), 1)
        self.assertEqual(services.level_from_xp(60), 2)
        self.assertEqual(services.level_from_xp(129), 2)
        self.assertEqual(services.level_from_xp(130), 3)

    def test_level_from_xp_if_maxed(self):
        self.assertEqual(services.level_from_xp(10 ** 9), services.MAX_LEVEL)

    def test_tier_from_level(self):
        self.assertEqual(services.tier_from_level(1), 'Pemula Sadar')
        self.assertEqual(services.tier_from_level(9), 'Pemula Sadar')
        self.assertEqual(services.tier_from_level(10), 'Pejuang Hijau')
        self.assertEqual(services.tier_from_level(20), 'Guardian Bumi')
        self.assertEqual(services.tier_from_level(35), 'Legenda Lestari')
        self.assertEqual(services.tier_from_level(50), 'Legenda Lestari')

    def test_next_tier(self):
        self.assertEqual(services.next_tier(1), (10, 'Pejuang Hijau'))
        self.assertEqual(services.next_tier(10), (20, 'Guardian Bumi'))
        self.assertIsNone(services.next_tier(35))

class XpTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('burhan', password='burunghantu123')
 
    def test_get_profile_creates_one_profile(self):
        first = services.get_profile(self.user)
        second = services.get_profile(self.user)

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(GameProfile.objects.filter(user=self.user).count(), 1)
        self.assertEqual((first.level, first.total_xp), (1, 0))
 
    def test_xp_progress(self):
        profile = services.get_profile(self.user)
        profile.total_xp = 30
        self.assertEqual(services.xp_progress(profile), {'current': 30, 'needed': 60, 'percent': 50})
 
    def test_xp_progress_if_maxed(self):
        profile = GameProfile.objects.create(user=self.user, level=services.MAX_LEVEL)
        self.assertEqual(services.xp_progress(profile), {'current': 0, 'needed': 0, 'percent': 100})
 
    def test_award_xp_without_level_up(self):
        result = services.award_xp(self.user, 20)
        self.assertEqual(result['level'], 1)
        self.assertFalse(result['leveled_up'])
        self.assertFalse(result['tier_changed'])
        self.assertEqual(services.get_profile(self.user).total_xp, 20)
 
    def test_award_xp_with_level_up(self):
        result = services.award_xp(self.user, 60)
        self.assertEqual(result['level'], 2)
        self.assertTrue(result['leveled_up'])
        self.assertFalse(result['tier_changed'])
 
    def test_award_xp_with_tier_change(self):
        result = services.award_xp(self.user, services.xp_floor(10))
        self.assertEqual(result['level'], 10)
        self.assertTrue(result['tier_changed'])
 
    def test_negative_xp_is_ignored(self):
        services.award_xp(self.user, 50)
        services.award_xp(self.user, -30)
        self.assertEqual(services.get_profile(self.user).total_xp, 50)