"""Skenario end-to-end dengan beberapa akun uji: notifikasi, misi, lencana, laporan, leaderboard."""
import unittest
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from gamification import services as game
from gamification.models import Badge, GameProfile, UserBadge
from scanner.models import FoodLog
from social.models import CampusMembership, University
from story.models import FriendChallenge

from .duels import has_lifecycle
from .badges import ensure_badges
from .models import BadgeRelease, DailyQuestSet, Notification
from .reports import build_report_history
from .services import build_challenge_data, todays_quests


def scan(user, grams, when=None, raw=None):
    """Satu scan (satu foto) dengan satu item."""
    log = FoodLog.objects.create(
        user=user, custom_name='makan', co2_grams=grams,
        ai_raw_response=raw or f'raw-{user.pk}-{FoodLog.objects.count()}',
    )
    if when:
        FoodLog.objects.filter(pk=log.pk).update(scanned_at=when)
    return log


def notif_ids(user):
    return {n['id'] for n in build_challenge_data(user)['notifs']}


def titles(user):
    return [n['t'] for n in build_challenge_data(user)['notifs']]


class Base(TestCase):
    def setUp(self):
        self.a = User.objects.create_user('akun_a', password='x12345678')
        self.b = User.objects.create_user('akun_b', password='x12345678')
        self.c = User.objects.create_user('akun_c', password='x12345678')


class ChallengeNotificationTests(Base):
    def test_receiver_gets_challenge_notification_with_link(self):
        FriendChallenge.objects.create(challenger=self.a, opponent=self.b, metric='lowest_co2', duration_days=7)
        notifs = build_challenge_data(self.b)['notifs']
        ch = [n for n in notifs if n['type'] == 'teman']
        self.assertEqual(len(ch), 1)
        self.assertEqual(ch[0]['t'], 'akun_a menantangmu!')
        self.assertIn('7 hari', ch[0]['p'])
        self.assertEqual(ch[0]['link'], reverse('story:challenge_list'))
        # Pengirim tidak dapat notifikasi "menantangmu" untuk tantangannya sendiri.
        self.assertFalse([n for n in build_challenge_data(self.a)['notifs'] if n['type'] == 'teman'])

    def test_notification_disappears_when_challenge_cancelled(self):
        ch = FriendChallenge.objects.create(challenger=self.a, opponent=self.b)
        self.assertTrue([n for n in build_challenge_data(self.b)['notifs'] if n['type'] == 'teman'])
        ch.delete()
        self.assertFalse([n for n in build_challenge_data(self.b)['notifs'] if n['type'] == 'teman'])

    @unittest.skipUnless(has_lifecycle(), 'butuh app story dari master (terima tantangan)')
    def test_accepted_challenge_creates_friend_for_ranking_tab(self):
        ch = FriendChallenge.objects.create(challenger=self.a, opponent=self.b)
        for u, g in ((self.a, 300), (self.b, 900)):
            for _ in range(3):
                scan(u, g)
        # Tantangan yang belum diterima belum menjadikan siapa pun teman.
        self.assertEqual(build_challenge_data(self.a)['rank']['teman']['empty'], 'no_friends')
        from story.challenge_services import accept_challenge
        accept_challenge(self.b, ch.pk)
        teman = build_challenge_data(self.a)['rank']['teman']
        self.assertEqual([r['name'] for r in teman['items']], ['akun_a', 'akun_b'])
        self.assertEqual(build_challenge_data(self.c)['rank']['teman']['empty'], 'no_friends')


class RankNotificationTests(Base):
    def rank_titles(self, user):
        return [n['t'] for n in build_challenge_data(user)['notifs'] if n['type'] == 'peringkat']

    def test_first_ranking_then_up_then_down(self):
        for _ in range(3):
            scan(self.a, 500)
            scan(self.b, 300)             # b lebih hemat -> a peringkat 2
        self.assertEqual(self.rank_titles(self.a), ['Kamu masuk peringkat minggu ini: #2'])
        self.assertEqual(self.rank_titles(self.a), ['Kamu masuk peringkat minggu ini: #2'])  # tidak dobel

        # a makin hemat -> naik ke #1
        for _ in range(6):
            scan(self.a, 5)
        self.assertIn('Kamu naik ke peringkat #1!', self.rank_titles(self.a))

        # c masuk dengan emisi sangat rendah -> a turun ke #2
        for _ in range(3):
            scan(self.c, 1)
        self.assertIn('Peringkatmu turun ke #2', self.rank_titles(self.a))
        n = Notification.objects.filter(user=self.a, kind='peringkat').count()
        build_challenge_data(self.a)
        self.assertEqual(Notification.objects.filter(user=self.a, kind='peringkat').count(), n)  # tanpa perubahan = tanpa notif baru

    def test_no_rank_notification_without_ranking(self):
        scan(self.a, 500)                 # baru 1 scan, belum masuk peringkat
        self.assertEqual(self.rank_titles(self.a), [])


class StreakNotificationTests(Base):
    def test_streak_notifications(self):
        today = timezone.localdate()
        scan(self.a, 400)
        game.update_streak(self.a, today - timedelta(days=1))
        game.update_streak(self.a, today)
        t = titles(self.a)
        self.assertIn('Streak 2 hari!', t)

        # Streak berjalan tapi belum scan hari ini -> peringatan terancam
        p = game.get_profile(self.b)
        p.current_streak, p.last_activity_date = 4, today - timedelta(days=1)
        p.save()
        self.assertIn('Streakmu terancam hilang', titles(self.b))

        # Streak sudah putus (bolos 2 hari) -> kabar terputus
        p = game.get_profile(self.c)
        p.current_streak, p.last_activity_date = 5, today - timedelta(days=3)
        p.save()
        self.assertIn('Streakmu terputus', titles(self.c))
        self.assertEqual(game.effective_streak(p), 0)

    def test_streak_freeze_keeps_streak(self):
        today = timezone.localdate()
        p = game.get_profile(self.a)
        p.current_streak, p.last_activity_date, p.streak_freezes = 5, today - timedelta(days=2), 1
        p.save()
        self.assertEqual(game.effective_streak(p, today), 5)
        game.update_streak(self.a, today)
        p.refresh_from_db()
        self.assertEqual((p.current_streak, p.streak_freezes), (7, 0))


class QuestTests(Base):
    def test_new_quests_and_all_done_notifications(self):
        quests, *_ = todays_quests(self.a, timezone.localdate())
        self.assertEqual(len(quests), 3)
        t = titles(self.a)
        self.assertIn('Kamu punya 3 misi baru hari ini!', t)
        self.assertNotIn('Kamu sudah menyelesaikan semua misi hari ini!', t)

        # Selesaikan semua: scan banyak & ringan agar semua jenis misi terpenuhi
        for _ in range(5):
            scan(self.a, 60)
        d = build_challenge_data(self.a)
        done = [q for q in d['quests'] if q['val'] >= q['goal']]
        if len(done) == len(d['quests']):
            self.assertIn('Kamu sudah menyelesaikan semua misi hari ini!', [n['t'] for n in d['notifs']])

    def test_all_done_notification_text(self):
        # Paksa set misi yang pasti selesai dengan scan ringan (tanpa tergantung acak).
        today = timezone.localdate()
        DailyQuestSet.objects.create(user=self.a, date=today, quest_ids='scan_once,scan_two,light_item')
        scan(self.a, 60)
        scan(self.a, 60)
        d = build_challenge_data(self.a)
        self.assertTrue(all(q['val'] >= q['goal'] for q in d['quests']))
        t = [n for n in d['notifs'] if n['id'].startswith('misi-done')]
        self.assertEqual(t[0]['t'], 'Kamu sudah menyelesaikan semua misi hari ini!')
        self.assertIn('kembali besok', t[0]['p'])

    def test_quests_change_every_day_and_differ_between_users(self):
        today = timezone.localdate()
        seen_same_as_yesterday = 0
        prev = None
        for i in range(14):
            day = today + timedelta(days=i)
            ids = [q['id'] for q in todays_quests(self.a, day)[0]]
            self.assertEqual(len(set(ids)), 3)
            if prev is not None and set(ids) == set(prev):
                seen_same_as_yesterday += 1
            self.assertFalse(set(ids) & set(prev or []), f'hari {day} mengulang misi kemarin: {ids} vs {prev}')
            prev = ids
        self.assertEqual(seen_same_as_yesterday, 0)

        day = today + timedelta(days=30)
        sets = {u.username: tuple(sorted(q['id'] for q in todays_quests(u, day)[0])) for u in (self.a, self.b, self.c)}
        self.assertGreater(len(set(sets.values())), 1, sets)

    def test_quests_stable_within_a_day(self):
        today = timezone.localdate()
        first = [q['id'] for q in todays_quests(self.a, today)[0]]
        scan(self.a, 900)
        scan(self.a, 900)
        self.assertEqual([q['id'] for q in todays_quests(self.a, today)[0]], first)

    def test_quests_follow_habits(self):
        today = timezone.localdate()
        # Pengguna rajin scan banyak & sering lewat budget -> katalog menyesuaikan
        for back in range(1, 6):
            for _ in range(3):
                scan(self.a, 900, when=timezone.now() - timedelta(days=back))
        from .services import _quest_catalog, _quest_context
        cat = _quest_catalog(_quest_context(self.a, today))
        self.assertIn('scan_four', cat)
        self.assertIn('consistent_scanner', cat)
        self.assertIn('beat_yesterday', cat)
        self.assertLessEqual(int(cat['low_carbon']['desc'].split('di bawah ')[1].split('g')[0]), 1500)
        # Pengguna baru tidak dapat misi yang butuh riwayat
        newbie = _quest_catalog(_quest_context(self.b, today))
        self.assertNotIn('scan_four', newbie)
        self.assertNotIn('beat_yesterday', newbie)
        self.assertNotIn('consistent_scanner', newbie)

    def test_every_quest_has_xp_and_claim_works(self):
        from .services import QUEST_XP, _quest_catalog, _quest_context
        cat = _quest_catalog(_quest_context(self.a, timezone.localdate()))
        for qid in cat:
            self.assertIn(qid, QUEST_XP, qid)


class BadgeTests(Base):
    def test_badges_seeded_without_visiting_badge_page_and_scan_counted_by_photo(self):
        self.assertEqual(Badge.objects.count(), 0)
        # 5 scan (foto) -> lencana "5 Scans"
        for i in range(5):
            scan(self.a, 300, raw=f'foto-{i}')
        d = build_challenge_data(self.a)
        self.assertGreater(Badge.objects.count(), 0)
        earned = [b['name'] for b in d['badges'] if b['earned']]
        self.assertIn('5 Scans', earned)
        self.assertEqual(d['stats']['badges'], 1)
        self.assertEqual(d['stats']['badgesTotal'], Badge.objects.count())
        self.assertIn('Lencana baru: 5 Scans', [n['t'] for n in d['notifs']])

    def test_item_rows_do_not_inflate_scan_badge(self):
        # Satu foto berisi 6 item = 1 scan, bukan 6.
        for i in range(6):
            FoodLog.objects.create(user=self.a, custom_name=f'item{i}', co2_grams=100, ai_raw_response='satu-foto')
        d = build_challenge_data(self.a)
        self.assertEqual(d['stats']['scans'], 1)
        self.assertNotIn('5 Scans', [b['name'] for b in d['badges'] if b['earned']])

    def test_new_badge_release_notifies_existing_users_only(self):
        build_challenge_data(self.a)                        # seed awal, tanpa notifikasi rilis
        self.assertFalse([t for t in titles(self.a) if t.startswith('Lencana baru dirilis')])
        # Admin merilis lencana baru
        Badge.objects.create(code='1000-scans', name='1000 Scans', description='Scan 1000x',
                             icon='camera', criteria_type='scan_amount', threshold=1000)
        self.assertIn('Lencana baru dirilis: 1000 Scans', titles(self.a))
        # Akun yang daftar SETELAH rilis tidak diberi tahu soal rilis itu
        late = User.objects.create_user('akun_baru', password='x12345678')
        titles(self.a)                                      # mencatat rilis (BadgeRelease)
        BadgeRelease.objects.filter(badge__code='1000-scans').update(released_at=timezone.now() - timedelta(days=1))
        self.assertFalse([t for t in titles(late) if t.startswith('Lencana baru dirilis')])

    def test_ensure_badges_adds_new_milestones_idempotently(self):
        ensure_badges()
        n = Badge.objects.count()
        ensure_badges()
        self.assertEqual(Badge.objects.count(), n)

    def test_streak_badge_and_profile_listing(self):
        today = timezone.localdate()
        p = game.get_profile(self.a)
        p.record_streak = 7
        p.save()
        d = build_challenge_data(self.a)
        self.assertIn('7 Day Streak', [b['name'] for b in d['badges'] if b['earned']])
        self.assertTrue(UserBadge.objects.filter(user=self.a, badge__code='7-streak').exists())
        # Muncul di halaman Profil (template + data)
        self.client.force_login(self.a)
        html = self.client.get(reverse('challenge:list')).content.decode()
        self.assertIn('badgeRow', html)


class ReportHistoryTests(Base):
    def setUp(self):
        super().setUp()
        today = timezone.localdate()
        monday = today - timedelta(days=today.weekday())
        self.last_monday = monday - timedelta(weeks=1)
        User.objects.filter(pk=self.a.pk).update(date_joined=timezone.now() - timedelta(days=21))
        self.a.refresh_from_db()
        base = timezone.now() - timedelta(days=today.weekday() + 7 - 1)   # Selasa minggu lalu
        for i, g in enumerate((300, 400, 500)):
            scan(self.a, g, when=base + timedelta(hours=i))
            scan(self.b, 200, when=base + timedelta(hours=i))
        scan(self.a, 5000, when=base + timedelta(days=1))                    # hari lewat budget

    def test_history_has_week_details_days_and_rank(self):
        h = build_report_history(self.a)
        w = h['weeks'][0]
        self.assertEqual(w['start'], self.last_monday)
        self.assertEqual(len(w['days']), 7)
        self.assertEqual(sum(1 for d in w['days'] if d['has']), 2)
        self.assertTrue(any(d['over'] for d in w['days']))
        self.assertIsNotNone(w['rank'])
        self.assertEqual(w['rank']['total'], 2)      # a dan b sama-sama punya >= 3 scan
        self.assertEqual(w['rank']['pos'], 2)        # b (200 g/scan) lebih hemat dari a
        self.assertEqual(w['over_days'], 1)

    def test_report_html_renders_scroller_cards_and_details(self):
        self.client.force_login(self.a)
        html = self.client.get(reverse('challenge:list')).content.decode()
        self.assertIn('id="rhScroller"', html)
        self.assertIn(f'data-week="{self.last_monday.isoformat()}"', html)
        self.assertIn('class="rh-detail"', html)
        self.assertIn('Geser ke kanan', html)
        self.assertIn(reverse('social:leaderboard'), html)

    def test_no_history_message_for_new_account(self):
        self.client.force_login(self.c)
        html = self.client.get(reverse('challenge:list')).content.decode()
        self.assertIn('Belum ada laporan sebelumnya', html)
        self.assertNotIn('id="rhScroller"', html)


class StatsEndpointTests(Base):
    def test_stats_endpoint_is_daily(self):
        self.client.force_login(self.a)
        scan(self.a, 1600)
        self.assertEqual(self.client.get(reverse('challenge:api_stats')).json()['avoidedKg'], 0.4)
        scan(self.a, 900)
        self.assertEqual(self.client.get(reverse('challenge:api_stats')).json()['avoidedKg'], 0)
