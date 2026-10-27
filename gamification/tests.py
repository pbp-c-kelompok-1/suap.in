from datetime import date, timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from gamification.models import *
from scanner.models import FoodLog

from . import services


def make_logs(user, count):
    for i in range(count):
        FoodLog.objects.create(user=user, custom_name=f'Item {i}', co2_grams=100)

class GamificationModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('burhan', password='burunghantu123')

    def test_defaults(self):
        profile = GameProfile.objects.create(user=self.user)
        self.assertEqual(profile.level, 1)
        self.assertEqual(profile.total_xp, 0)
        self.assertEqual(profile.streak_freezes, 0)
        self.assertIn('Lvl 1', str(profile))
    
    def test_get_profile_creates_one_profile(self):
        first = services.get_profile(self.user)
        second = services.get_profile(self.user)

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(GameProfile.objects.filter(user=self.user).count(), 1)

    def test_level_check_constraints(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                GameProfile.objects.create(user=self.user, level=0)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                GameProfile.objects.create(user=self.user, level=67)

    def test_unique_user_badges(self):
        badge = Badge.objects.create(code='dummy', name='dummy', threshold=67)
        UserBadge.objects.create(user=self.user, badge=badge)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                UserBadge.objects.create(user=self.user, badge=badge)

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

class BadgeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('burhan', password='burunghantu123')
        services.seedBadges()

    # Material
    def test_material_for_scans(self):
        self.assertEqual(services.badge_material_from_threshold('scan_amount', 5), 'bronze')
        self.assertEqual(services.badge_material_from_threshold('scan_amount', 50), 'silver')
        self.assertEqual(services.badge_material_from_threshold('scan_amount', 250), 'gold')
 
    def test_material_for_streaks(self):
        self.assertEqual(services.badge_material_from_threshold('streak_duration', 7), 'bronze')
        self.assertEqual(services.badge_material_from_threshold('streak_duration', 30), 'silver')
        self.assertEqual(services.badge_material_from_threshold('streak_duration', 180), 'gold')
 
    def test_material_for_unknown_criteria(self):
        self.assertEqual(services.badge_material_from_threshold('unknown', 5), '')

    # Rarity
    def test_rarity(self):
        self.assertEqual(services.badge_rarity('scan_amount', 10), 0)
        self.assertEqual(services.badge_rarity('scan_amount', 100), 1)
        self.assertEqual(services.badge_rarity('scan_amount', 500), 2)
        self.assertEqual(services.badge_rarity('streak_duration', 7), 0)
        self.assertEqual(services.badge_rarity('streak_duration', 30), 1)
        self.assertEqual(services.badge_rarity('streak_duration', 365), 2)

    def test_rarity_for_unknown_criteria(self):
        self.assertEqual(services.badge_rarity('unknown', 0), 0)

    def test_badge_seeding_seeds_all_badges(self):
        expected = len(services.STREAK_MILESTONES) + len(services.SCAN_MILESTONES)
        self.assertEqual(Badge.objects.count(), expected)
 
    def test_badge_seeding_twice_shouldnt_change(self):
        before = Badge.objects.count()
        services.seedBadges()
        self.assertEqual(Badge.objects.count(), before)

    def test_no_badges_unlocked(self):
        self.assertEqual(services.check_badges(self.user), [])
        self.assertEqual(UserBadge.objects.filter(user=self.user).count(), 0)

    def test_badge_being_rewarded(self):
        make_logs(self.user, 5)
        unlocked_badges = services.check_badges(self.user)
        self.assertEqual([badge.code for badge in unlocked_badges], ['5-scans'])
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge__code='5-scans').exists())

    def test_no_duplicate_badges(self):
        make_logs(self.user, 5)
        services.check_badges(self.user)
        self.assertEqual(services.check_badges(self.user), [])
        self.assertEqual(UserBadge.objects.filter(user=self.user).count(), 1)

class ScannerInteractionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('burhan', password='burunghantu123')
        services.seedBadges()

    def test_record_scan_output(self):
        make_logs(self.user, 5)
        output = services.record_scan(self.user, 12)
        self.assertEqual(output['xp_gained'], 12)
        self.assertEqual(output['streak'], 1)
        self.assertEqual(output['level'], 1)
        self.assertFalse(output['leveled_up'])
        self.assertEqual([badge.code for badge in output['new_badges']], ['5-scans'])

    def test_record_scan_can_level_up(self):
        output = services.record_scan(self.user, 60)
        self.assertTrue(output['leveled_up'])
        self.assertEqual(output['level'], 2)

class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('burhan', password='burunghantu123')
        self.url = reverse('gamification:dashboard')
 
    def test_guest_sees_landing(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Daftar gratis')
 
    def test_authenticated_context_for_new_user(self):
        self.client.login(username='burhan', password='burunghantu123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['streak'], 0)
        self.assertFalse(response.context['scanned_today'])
        self.assertEqual(response.context['level'], 1)
        self.assertEqual(response.context['tier_name'], 'Pemula Sadar')
        self.assertEqual(response.context['used_grams'], 0.0)
 
    def test_context_after_record_scan(self):
        self.client.login(username='burhan', password='burunghantu123')
        services.record_scan(self.user, xp=10)
        response = self.client.get(self.url)
        self.assertTrue(response.context['scanned_today'])
        self.assertEqual(response.context['streak'], 1)

class StreakViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('burhan', password='burunghantu123')
        self.url = reverse('gamification:streak')
 
    def test_guest_gets_page(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Masuk untuk melihat streak')
 
    def test_week_widget(self):
        self.client.login(username='burhan', password='burunghantu123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['streak'], 0)
        self.assertEqual(len(response.context['week']), 7)
        self.assertEqual(response.context['next_goal'], services.STREAK_MILESTONES[0])
        self.assertEqual(response.context['week_done'], 0)
 
    def test_week_widget_done_mark_if_scanned_today(self):
        self.client.login(username='burhan', password='burunghantu123')
        make_logs(self.user, 1)
        services.update_streak(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.context['streak'], 1)
        self.assertTrue(response.context['scanned_today'])
        self.assertEqual(response.context['week_done'], 1)
        today_entry = next(d for d in response.context['week'] if d['is_today'])
        self.assertEqual(today_entry['state'], 'done')
        self.assertEqual(response.context['days_left'], services.STREAK_MILESTONES[0] - 1)
 
    def test_next_goal(self):
        self.client.login(username='burhan', password='burunghantu123')
        today = timezone.localdate()
        GameProfile.objects.create(user=self.user, current_streak=7, record_streak=7, last_activity_date=today)
        response = self.client.get(self.url)
        self.assertEqual(response.context['next_goal'], 14)
        self.assertEqual(response.context['goal_percent'], 50)

class LevelViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('burhan', password='burunghantu123')
        self.url = reverse('gamification:level')
 
    def test_guest_gets_page(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Masuk untuk melihat level')
 
    def test_new_user_tiers(self):
        self.client.login(username='burhan', password='burunghantu123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        tiers = response.context['tiers']

        self.assertEqual(len(tiers), len(services.TIERS))
        self.assertEqual(tiers[0]['state'], 'current')
        self.assertEqual([t['state'] for t in tiers[1:]], ['locked'] * 3)
        self.assertEqual(response.context['tier_name'], 'Pemula Sadar')
        self.assertEqual(response.context['reached_count'], 1)
        self.assertEqual(response.context['xp_to_next'], 60)
 
    def test_high_level_marks_lower_tiers_reached(self):
        self.client.login(username='burhan', password='burunghantu123')
        GameProfile.objects.create(user=self.user, level=22, total_xp=services.xp_floor(22))
        response = self.client.get(self.url)
        states = [t['state'] for t in response.context['tiers']]

        self.assertEqual(states, ['reached', 'reached', 'current', 'locked'])
        self.assertEqual(response.context['tier_name'], 'Guardian Bumi')
        self.assertEqual(response.context['tiers'][3]['levels_left'], 13)
 
    def test_max_level(self):
        self.client.login(username='burhan', password='burunghantu123')
        GameProfile.objects.create(user=self.user, level=services.MAX_LEVEL)
        response = self.client.get(self.url)
        self.assertTrue(response.context['is_max_level'])
        self.assertEqual(response.context['xp_to_next'], 0)


class BadgeViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('burhan', password='burunghantu123')
        self.api = reverse('gamification:get_badges_json')
 
    def test_badges_page_opens_for_guest(self):
        self.assertEqual(self.client.get(reverse('gamification:badges')).status_code, 200)
 
    def test_api_requires_login(self):
        response = self.client.get(self.api)
        self.assertEqual(response.status_code, 401)
        self.assertIn('error', response.json())
 
    def test_api_all_badges_locked_for_new_user(self):
        self.client.login(username='burhan', password='burunghantu123')
        data = self.client.get(self.api).json()
        total = len(services.STREAK_MILESTONES) + len(services.SCAN_MILESTONES)
        self.assertEqual(data['unlocked'], [])
        self.assertEqual(len(data['locked']), total)
 
    def test_api_moves_earned_badge_to_unlocked(self):
        self.client.login(username='burhan', password='burunghantu123')
        make_logs(self.user, 5)

        data = self.client.get(self.api).json()
        unlocked = {badge['code']: badge for badge in data['unlocked']}

        self.assertEqual(list(unlocked), ['5-scans'])
        fields = unlocked['5-scans']['fields']
        self.assertEqual(fields['type'], 'scan_amount')
        self.assertEqual(fields['material'], 'bronze')
        self.assertEqual(fields['rarity'], 0)
        self.assertIn('earned_at', fields)

        self.assertNotIn('5-scans', [b['code'] for b in data['locked']])
 
    def test_badges_page_awards_pending_badges(self):
        self.client.login(username='burhan', password='burunghantu123')
        services.seedBadges()
        make_logs(self.user, 5)
        self.client.get(reverse('gamification:badges'))
        
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge__code='5-scans').exists())