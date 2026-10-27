from datetime import date, timedelta

from django.test import TestCase
from django.contrib.auth.models import User

from gamification.models import *
from scanner.models import FoodLog

from . import services


def make_logs(user, count):
    for i in range(count):
        FoodLog.objects.create(user=user, custom_name=f'Item {i}', co2_grams=100)


class LevelServiceTests(TestCase):
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

class XpServiceTests(TestCase):
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

class StreakTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('burhan', password='burunghantu123')
        self.today = date(2026, 6, 7)
 
    def profile(self):
        return GameProfile.objects.get(user=self.user)

    # Updating Streaks
    def test_update_streak_starts_streak(self):
        profile = services.update_streak(self.user, self.today)
        self.assertEqual(profile.current_streak, 1)
        self.assertEqual(profile.record_streak, 1)
        self.assertEqual(profile.last_activity_date, self.today)
 
    def test_update_streak_twice_does_not_increments_streak(self):
        services.update_streak(self.user, self.today)
        services.update_streak(self.user, self.today)
        self.assertEqual(self.profile().current_streak, 1)
 
    def test_update_streak_on_consecutive_days_increments_streak(self):
        services.update_streak(self.user, self.today)
        services.update_streak(self.user, self.today + timedelta(days=1))
        profile = services.update_streak(self.user, self.today + timedelta(days=2))
        self.assertEqual(profile.current_streak, 3)
        self.assertEqual(profile.record_streak, 3)

    def test_streak_record(self):
        services.update_streak(self.user, self.today)
        services.update_streak(self.user, self.today + timedelta(days=1))
        profile = services.update_streak(self.user, self.today + timedelta(days=4))
        self.assertEqual(profile.current_streak, 1)
        self.assertEqual(profile.record_streak, 2)

    # Streak Freeze
    def test_freeze_covers_one_day(self):
        services.update_streak(self.user, self.today)
        GameProfile.objects.filter(user=self.user).update(streak_freezes=1)
        profile = services.update_streak(self.user, self.today + timedelta(days=2))
        self.assertEqual(profile.streak_freezes, 0)
        self.assertEqual(profile.current_streak, 3)
 
    def test_not_enough_freezes_resets_streak(self):
        services.update_streak(self.user, self.today)
        GameProfile.objects.filter(user=self.user).update(streak_freezes=1)
        profile = services.update_streak(self.user, self.today + timedelta(days=3))
        self.assertEqual(profile.current_streak, 1)
        self.assertEqual(profile.streak_freezes, 1)

    # Effective Streak
    def test_effective_streak_without_activity(self):
        profile = services.get_profile(self.user)
        self.assertEqual(services.effective_streak(profile, self.today), 0)
 
    def test_effective_streak_when_alive_and_broken(self):
        services.update_streak(self.user, self.today)
        profile = self.profile()
        self.assertEqual(services.effective_streak(profile, self.today), 1)
        self.assertEqual(services.effective_streak(profile, self.today + timedelta(days=1)), 1)
        self.assertEqual(services.effective_streak(profile, self.today + timedelta(days=3)), 0)
 
    def test_effective_streak_protected_by_freezes(self):
        services.update_streak(self.user, self.today)
        GameProfile.objects.filter(user=self.user).update(streak_freezes=2)
        profile = self.profile()
        self.assertEqual(services.effective_streak(profile, self.today + timedelta(days=3)), 1)

    # Streak Freeze Claiming
    def test_claim_success(self):
        success, message = services.claim_streak_freeze(self.user, self.today)
        self.assertTrue(success)
        self.assertEqual(message, '')
        profile = services.get_profile(self.user)
        self.assertEqual(profile.streak_freezes, 1)
        self.assertEqual(profile.freezes_claimed_this_week, 1)
 
    def test_claim_fail_due_to_weekly_limit(self):
        services.claim_streak_freeze(self.user, self.today)
        services.claim_streak_freeze(self.user, self.today)
        success, message = services.claim_streak_freeze(self.user, self.today)
        self.assertFalse(success)
        self.assertIn('Batas klaim', message)
 
    def test_claim_fail_due_to_max_freezes_in_inventory(self):
        GameProfile.objects.create(user=self.user, streak_freezes=services.MAX_STORED_FREEZES)
        success, message = services.claim_streak_freeze(self.user, self.today)
        self.assertFalse(success)
        self.assertIn('maksimal', message)
 
    def test_weekly_limit_resets_next_week(self):
        services.claim_streak_freeze(self.user, self.today)
        services.claim_streak_freeze(self.user, self.today)
        GameProfile.objects.filter(user=self.user).update(streak_freezes=0)
        success, _ = services.claim_streak_freeze(self.user, self.today + timedelta(days=7))
        self.assertTrue(success)
        self.assertEqual(services.get_profile(self.user).freezes_claimed_this_week, 1)