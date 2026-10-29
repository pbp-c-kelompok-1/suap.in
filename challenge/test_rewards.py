import json
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from scanner.models import FoodLog

from .models import QuestClaim
from .services import build_challenge_data, count_scans, saved_budget_grams, saved_today_grams


def post_json(client, url, payload):
    return client.post(url, data=json.dumps(payload), content_type='application/json')


class ScanCountTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('nami', password='x12345678')

    def test_items_from_one_photo_count_as_one_scan(self):
        for name in ('Nasi', 'Ayam', 'Sayur', 'Telur', 'Tahu'):
            FoodLog.objects.create(
                user=self.user, custom_name=name, co2_grams=100,
                ai_raw_response='{"foto": "satu"}',
            )

        self.assertEqual(count_scans(FoodLog.objects.filter(user=self.user)), 1)
        data = build_challenge_data(self.user)
        self.assertEqual(data['totalScans'], 1)
        self.assertEqual(data['scansToday'], 1)

    def test_separate_photos_count_separately(self):
        FoodLog.objects.create(user=self.user, custom_name='Nasi', co2_grams=100, ai_raw_response='foto-1')
        FoodLog.objects.create(user=self.user, custom_name='Mie', co2_grams=100, ai_raw_response='foto-2')
        FoodLog.objects.create(user=self.user, custom_name='Roti', co2_grams=100)  # tanpa respons AI
        self.assertEqual(build_challenge_data(self.user)['totalScans'], 3)


class WeekAndBudgetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('nami', password='x12345678')

    def test_week_is_fixed_monday_to_sunday(self):
        data = build_challenge_data(self.user)
        start = date.fromisoformat(data['weekRange']['start'])
        end = date.fromisoformat(data['weekRange']['end'])
        self.assertEqual(start.weekday(), 0)
        self.assertEqual(end, start + timedelta(days=6))
        self.assertEqual(
            [w['d'] for w in data['weekly']],
            ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min'],
        )

    def test_saved_budget_counts_today_and_follows_new_scans(self):
        today = timezone.localdate()
        FoodLog.objects.create(user=self.user, custom_name='sarapan', co2_grams=500)
        self.assertEqual(saved_budget_grams(self.user, today), 1500)      # 2000 - 500

        FoodLog.objects.create(user=self.user, custom_name='makan siang', co2_grams=800)
        self.assertEqual(saved_budget_grams(self.user, today), 700)       # 2000 - 1300

        FoodLog.objects.create(user=self.user, custom_name='makan malam', co2_grams=1200)
        self.assertEqual(saved_budget_grams(self.user, today), 0)         # lewat budget -> 0, bukan minus

    def test_saved_budget_adds_up_finished_days_and_today(self):
        today = timezone.localdate()
        kemarin = FoodLog.objects.create(user=self.user, custom_name='kemarin', co2_grams=1500)
        FoodLog.objects.filter(pk=kemarin.pk).update(scanned_at=timezone.now() - timedelta(days=1))
        FoodLog.objects.create(user=self.user, custom_name='hari ini', co2_grams=1300)
        self.assertEqual(saved_budget_grams(self.user, today), 500 + 700)

    def test_stats_in_challenge_data_update_after_new_scan(self):
        FoodLog.objects.create(user=self.user, custom_name='a', co2_grams=500)
        self.assertEqual(build_challenge_data(self.user)['stats']['avoidedKg'], 1.5)
        FoodLog.objects.create(user=self.user, custom_name='b', co2_grams=1000)
        self.assertEqual(build_challenge_data(self.user)['stats']['avoidedKg'], 0.5)

    def test_saved_today_ignores_other_days_and_hits_zero_when_over(self):
        today = timezone.localdate()
        kemarin = FoodLog.objects.create(user=self.user, custom_name='kemarin', co2_grams=1500)
        FoodLog.objects.filter(pk=kemarin.pk).update(scanned_at=timezone.now() - timedelta(days=1))
        self.assertEqual(saved_today_grams(self.user, today), 0)          # belum scan hari ini
        FoodLog.objects.create(user=self.user, custom_name='a', co2_grams=1600)
        self.assertEqual(saved_today_grams(self.user, today), 400)        # 2000 - 1600
        FoodLog.objects.create(user=self.user, custom_name='b', co2_grams=900)
        self.assertEqual(saved_today_grams(self.user, today), 0)          # lewat budget -> 0

    def test_saved_budget_is_zero_when_over_budget(self):
        today = timezone.localdate()
        log = FoodLog.objects.create(user=self.user, custom_name='boros', co2_grams=3000)
        FoodLog.objects.filter(pk=log.pk).update(scanned_at=timezone.now() - timedelta(days=1))
        self.assertEqual(saved_budget_grams(self.user, today), 0)


class QuestClaimTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('nami', password='x12345678')
        self.client.force_login(self.user)
        FoodLog.objects.create(user=self.user, custom_name='Salad', co2_grams=100)
        self.url = reverse('challenge:claim_quest')

    def quests(self):
        return build_challenge_data(self.user)['quests']

    def test_claim_is_manual_and_only_once(self):
        done = [q for q in self.quests() if q['val'] >= q['goal']]
        self.assertTrue(done)
        quest = done[0]
        self.assertFalse(quest['claimed'])

        res = post_json(self.client, self.url, {'quest_id': quest['id']})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['xp'], quest['xp'])
        self.assertEqual(QuestClaim.objects.filter(user=self.user).count(), 1)

        again = post_json(self.client, self.url, {'quest_id': quest['id']})
        self.assertEqual(again.status_code, 400)
        self.assertEqual(QuestClaim.objects.filter(user=self.user).count(), 1)

    def test_cannot_claim_unfinished_quest(self):
        todo = [q for q in self.quests() if q['val'] < q['goal']]
        if not todo:
            self.skipTest('Semua misi hari ini sudah selesai.')
        res = post_json(self.client, self.url, {'quest_id': todo[0]['id']})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(QuestClaim.objects.count(), 0)


class NotificationPersistenceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('nami', password='x12345678')
        self.client.force_login(self.user)
        FoodLog.objects.create(user=self.user, custom_name='Salad', co2_grams=100)

    def notifs(self):
        return build_challenge_data(self.user)['notifs']

    def test_read_state_is_kept_and_not_duplicated(self):
        first = self.notifs()
        self.assertTrue(first)
        key = first[0]['id']
        self.assertFalse(first[0]['read'])

        post_json(self.client, reverse('challenge:notif_read'), {'ids': [key]})

        again = [n for n in self.notifs() if n['id'] == key]
        self.assertEqual(len(again), 1)
        self.assertTrue(again[0]['read'])

    def test_read_all(self):
        self.notifs()
        post_json(self.client, reverse('challenge:notif_read'), {'all': True})
        self.assertTrue(all(n['read'] for n in self.notifs()))

    def test_dismissed_notification_stays_gone(self):
        key = self.notifs()[0]['id']
        post_json(self.client, reverse('challenge:notif_dismiss'), {'id': key})
        self.assertNotIn(key, [n['id'] for n in self.notifs()])
        self.assertNotIn(key, [n['id'] for n in self.notifs()])
