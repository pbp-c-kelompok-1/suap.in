from datetime import date, datetime, time, timedelta
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from scanner.models import FoodLog
from social.models import CampusMembership, University

from .models import ChallengeProfile
from .ranking import (
    HISTORY_WEEKS,
    LIVE_NOTICE,
    MIN_SCANS_FOR_RANK,
    TOP_N,
    build_rankings,
    build_weekly_ranking_recap,
    week_start,
)

TODAY = date(2026, 10, 28)  # Rabu; minggu ini = 26 Okt - 1 Nov 2026
MONDAY = week_start(TODAY)
LAST_MONDAY = MONDAY - timedelta(weeks=1)


def make_user(name):
    return User.objects.create_user(name, f'{name}@example.com', 'pw')


def scan(user, day, grams, n=1):
    """Buat n scan pada tanggal `day` (scanned_at auto_now_add, jadi di-update)."""
    for i in range(n):
        log = FoodLog.objects.create(user=user, custom_name='x', co2_grams=grams)
        when = timezone.make_aware(datetime.combine(day, time(8 + i, 0)))
        FoodLog.objects.filter(pk=log.pk).update(scanned_at=when)


class WeeklyRankingTests(TestCase):
    def test_user_without_scans_is_never_ranked(self):
        # Bug lama: user tanpa scan (total NULL/0) menjadi peringkat 1.
        me = make_user('me')
        make_user('lazy')
        a = make_user('a')
        scan(a, MONDAY, 500, n=MIN_SCANS_FOR_RANK)
        scan(me, MONDAY, 800, n=MIN_SCANS_FOR_RANK)

        items = build_rankings(me, TODAY)['rank']['nasional']['items']
        self.assertEqual([i['name'] for i in items], ['a', 'me'])

    def test_lower_average_ranks_higher_and_volume_is_fair(self):
        me = make_user('me')
        heavy_scanner = make_user('heavy')
        one_meal = make_user('three')
        scan(heavy_scanner, MONDAY, 300, n=7)   # rata-rata 300, banyak scan
        scan(one_meal, MONDAY, 350, n=3)        # rata-rata 350, total lebih kecil
        scan(me, MONDAY, 900, n=3)

        items = build_rankings(me, TODAY)['rank']['nasional']['items']
        self.assertEqual([i['name'] for i in items], ['heavy', 'three', 'me'])
        self.assertEqual([i['pos'] for i in items], [1, 2, 3])
        self.assertTrue(items[2]['is_me'])
        self.assertEqual(items[0]['avg'], 300)

    def test_tie_prefers_more_scans_then_username(self):
        me = make_user('me')
        b = make_user('b')
        a = make_user('a')
        scan(me, MONDAY, 400, n=3)
        scan(b, MONDAY, 400, n=4)
        scan(a, MONDAY, 400, n=3)
        items = build_rankings(me, TODAY)['rank']['nasional']['items']
        self.assertEqual([i['name'] for i in items], ['b', 'a', 'me'])

    def test_only_current_week_counts_for_current_ranking(self):
        me = make_user('me')
        other = make_user('other')
        scan(me, MONDAY, 600, n=3)
        scan(other, LAST_MONDAY, 100, n=3)   # minggu lalu, tidak boleh masuk
        data = build_rankings(me, TODAY)['rank']['nasional']
        self.assertEqual([i['name'] for i in data['items']], ['me'])
        self.assertEqual(data['total'], 1)

    def test_empty_flow_codes(self):
        me = make_user('me')
        r = build_rankings(me, TODAY)['rank']
        self.assertEqual(r['nasional']['empty'], 'no_scan')          # belum pernah scan
        self.assertEqual(r['kampus']['empty'], 'no_campus')          # kampus dicek duluan
        self.assertEqual(r['teman']['empty'], 'no_friends')

        uni = University.objects.create(name='Universitas X', short_name='UX')
        CampusMembership.objects.create(user=me, university=uni)
        r = build_rankings(me, TODAY)['rank']
        self.assertEqual(r['kampus']['empty'], 'no_scan')            # sudah pilih kampus, belum scan

        scan(me, LAST_MONDAY, 500)                                   # pernah scan, tapi bukan minggu ini
        r = build_rankings(me, TODAY)['rank']
        self.assertEqual(r['kampus']['empty'], 'no_scan_week')

        scan(me, MONDAY, 500)
        r = build_rankings(me, TODAY)['rank']
        self.assertEqual(r['kampus']['empty'], 'few_scans')
        self.assertEqual(r['kampus']['need'], MIN_SCANS_FOR_RANK - 1)

        scan(me, MONDAY, 500, n=MIN_SCANS_FOR_RANK - 1)
        r = build_rankings(me, TODAY)['rank']
        self.assertEqual(r['kampus']['empty'], '')
        self.assertEqual(r['kampus']['position'], 1)

    def test_campus_scope_only_same_university(self):
        uni_a = University.objects.create(name='Uni A', short_name='UA')
        uni_b = University.objects.create(name='Uni B', short_name='UB')
        me, mate, stranger = make_user('me'), make_user('mate'), make_user('stranger')
        CampusMembership.objects.create(user=me, university=uni_a)
        CampusMembership.objects.create(user=mate, university=uni_a)
        CampusMembership.objects.create(user=stranger, university=uni_b)
        scan(me, MONDAY, 500, n=3)
        scan(mate, MONDAY, 400, n=3)
        scan(stranger, MONDAY, 100, n=3)

        r = build_rankings(me, TODAY)
        self.assertEqual([i['name'] for i in r['rank']['kampus']['items']], ['mate', 'me'])
        self.assertEqual(r['campusRank'], 2)
        self.assertEqual(
            [i['name'] for i in r['rank']['nasional']['items']], ['stranger', 'mate', 'me']
        )

    def test_me_outside_top_n_is_appended_with_real_position(self):
        me = make_user('me')
        scan(me, MONDAY, 5000, n=3)
        for i in range(TOP_N + 2):
            scan(make_user(f'u{i:02d}'), MONDAY, 100 + i, n=3)

        items = build_rankings(me, TODAY)['rank']['nasional']['items']
        self.assertEqual(len(items), TOP_N + 1)
        self.assertTrue(items[-1]['is_me'])
        self.assertEqual(items[-1]['pos'], TOP_N + 3)

    def test_display_name_and_avatar_come_from_profile(self):
        me = make_user('me')
        other = make_user('other')
        ChallengeProfile.objects.create(user=other, display_name='Budi', avatar_id=23)
        scan(me, MONDAY, 900, n=3)
        scan(other, MONDAY, 100, n=3)
        items = build_rankings(me, TODAY)['rank']['nasional']['items']
        self.assertEqual((items[0]['name'], items[0]['avatar']), ('Budi', 23))

    def test_recap_message_period_and_delta(self):
        me = make_user('me')
        rival = make_user('rival')
        # minggu lalu: rival #1, me #2
        scan(rival, LAST_MONDAY, 100, n=3)
        scan(me, LAST_MONDAY, 200, n=3)
        # minggu ini: me #1
        scan(me, MONDAY, 100, n=3)
        scan(rival, MONDAY, 300, n=3)

        recap = build_weekly_ranking_recap(me, TODAY)
        self.assertEqual(recap['weekStart'], '2026-10-26')
        self.assertEqual(recap['weekEnd'], '2026-11-01')
        self.assertEqual((recap['position'], recap['totalUsers']), (1, 2))
        self.assertEqual(recap['delta'], 1)
        self.assertEqual(recap['tone'], 'top')
        self.assertIn('nomor 1', recap['message'])
        self.assertIn('Naik 1 peringkat', recap['message'])
        self.assertEqual([t['name'] for t in recap['top']], ['me', 'rival'])

    def test_recap_encourages_when_ranked_low(self):
        me = make_user('me')
        scan(me, MONDAY, 9000, n=3)
        for i in range(5):
            scan(make_user(f'u{i}'), MONDAY, 100 + i, n=3)
        recap = build_weekly_ranking_recap(me, TODAY)
        self.assertEqual(recap['position'], 6)
        self.assertEqual(recap['tone'], 'push')
        self.assertIn('Semangat', recap['message'])

    def test_recap_when_not_ranked(self):
        me = make_user('me')
        self.assertIsNone(build_weekly_ranking_recap(me, TODAY)['position'])
        scan(me, MONDAY, 500)
        recap = build_weekly_ranking_recap(me, TODAY)
        self.assertIsNone(recap['position'])
        self.assertEqual(recap['tone'], 'start')
        self.assertIn(str(MIN_SCANS_FOR_RANK - 1), recap['message'])

    def test_history_lists_finished_weeks_with_dates_newest_first(self):
        me = make_user('me')
        other = make_user('other')
        two_weeks_ago = MONDAY - timedelta(weeks=2)
        scan(me, two_weeks_ago, 300, n=3)
        scan(other, two_weeks_ago, 100, n=3)
        scan(me, LAST_MONDAY, 300, n=1)          # hanya 1 scan -> belum masuk peringkat
        scan(me, MONDAY, 300, n=3)               # minggu berjalan tidak masuk riwayat

        history = build_weekly_ranking_recap(me, TODAY)['history']
        self.assertEqual([h['weekStart'] for h in history], ['2026-10-19', '2026-10-12'])
        self.assertEqual(history[0]['weekEnd'], '2026-10-25')
        self.assertEqual(history[0]['status'], 'few')
        self.assertEqual(history[1]['status'], 'ranked')
        self.assertEqual((history[1]['position'], history[1]['total']), (2, 2))

    def test_history_is_limited_to_window_and_empty_without_scans(self):
        me = make_user('me')
        self.assertEqual(build_weekly_ranking_recap(me, TODAY)['history'], [])
        too_old = MONDAY - timedelta(weeks=HISTORY_WEEKS + 2)
        scan(me, too_old, 300, n=3)
        self.assertEqual(build_weekly_ranking_recap(me, TODAY)['history'], [])


class FriendScopeAndLiveNoticeTests(TestCase):
    def test_friends_tab_is_empty_until_friend_system_exists(self):
        me = make_user('me')
        scan(me, MONDAY, 400, n=3)
        scan(make_user('stranger'), MONDAY, 100, n=3)
        teman = build_rankings(me, TODAY)['rank']['teman']
        self.assertEqual(teman['empty'], 'no_friends')
        self.assertEqual(teman['items'], [])

    def test_friends_tab_only_contains_accepted_friends_and_me(self):
        me, friend, stranger = make_user('me'), make_user('friend'), make_user('stranger')
        scan(me, MONDAY, 500, n=3)
        scan(friend, MONDAY, 400, n=3)
        scan(stranger, MONDAY, 100, n=3)      # paling hijau, tapi bukan teman

        with mock.patch('challenge.ranking.friend_user_ids', return_value={friend.pk}):
            r = build_rankings(me, TODAY)['rank']
        self.assertEqual([i['name'] for i in r['teman']['items']], ['friend', 'me'])
        self.assertEqual(r['teman']['position'], 2)
        # nasional tetap berisi semua akun yang ikut bertanding
        self.assertEqual([i['name'] for i in r['nasional']['items']], ['stranger', 'friend', 'me'])

    def test_friend_tab_ignores_unknown_ids_and_non_scanning_friends(self):
        me, lazy_friend = make_user('me'), make_user('lazy')
        scan(me, MONDAY, 500, n=3)
        with mock.patch('challenge.ranking.friend_user_ids', return_value={lazy_friend.pk, 999999}):
            teman = build_rankings(me, TODAY)['rank']['teman']
        self.assertEqual([i['name'] for i in teman['items']], ['me'])

    def test_friend_rank_follows_same_flow_as_other_tabs(self):
        me, friend = make_user('me'), make_user('friend')
        scan(friend, MONDAY, 100, n=3)
        with mock.patch('challenge.ranking.friend_user_ids', return_value={friend.pk}):
            self.assertEqual(build_rankings(me, TODAY)['rank']['teman']['empty'], 'no_scan')
            scan(me, MONDAY, 500, n=1)
            self.assertEqual(build_rankings(me, TODAY)['rank']['teman']['empty'], 'few_scans')

    def test_live_notice_only_for_ranked_users_with_days_left(self):
        me, idle = make_user('me'), make_user('idle')
        scan(me, MONDAY, 300, n=3)
        notice = build_weekly_ranking_recap(me, TODAY)['liveNotice']
        self.assertTrue(notice.startswith(LIVE_NOTICE))
        self.assertIn('Sisa 4 hari lagi', notice)          # Rabu -> Minggu
        self.assertIsNone(build_weekly_ranking_recap(idle, TODAY)['liveNotice'])

    def test_live_notice_on_last_day(self):
        me = make_user('me')
        sunday = MONDAY + timedelta(days=6)
        scan(me, MONDAY, 300, n=3)
        notice = build_weekly_ranking_recap(me, sunday)['liveNotice']
        self.assertIn('Hari ini hari terakhir', notice)

    def test_ranking_is_stable_across_repeated_calls(self):
        me = make_user('me')
        scan(me, MONDAY, 300, n=3)
        for i in range(6):
            scan(make_user(f'u{i}'), MONDAY, 200 + i * 10, n=3)
        first = build_rankings(me, TODAY)
        for _ in range(3):
            self.assertEqual(build_rankings(me, TODAY), first)
