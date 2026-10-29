from datetime import date, datetime, time, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from scanner.models import FoodLog

from .reports import REPORT_HISTORY_WEEKS, build_report_history

TODAY = date(2026, 10, 28)                  # Rabu
MONDAY = TODAY - timedelta(days=TODAY.weekday())   # 26 Okt 2026


def aware(day, hour=9):
    return timezone.make_aware(datetime.combine(day, time(hour, 0)))


def make_user(joined_day):
    user = User.objects.create_user('nami', password='x12345678')
    User.objects.filter(pk=user.pk).update(date_joined=aware(joined_day))
    user.refresh_from_db()
    return user


def scan(user, day, grams, raw=''):
    log = FoodLog.objects.create(user=user, custom_name='x', co2_grams=grams, ai_raw_response=raw)
    FoodLog.objects.filter(pk=log.pk).update(scanned_at=aware(day))


class ReportHistoryTests(TestCase):
    def test_new_user_has_no_history_yet(self):
        user = make_user(MONDAY)                       # baru daftar minggu ini
        scan(user, TODAY, 500)
        h = build_report_history(user, TODAY)
        self.assertEqual(h['weeks'], [])
        self.assertEqual(h['weeks_with_data'], 0)

    def test_history_starts_at_signup_week_and_excludes_current_week(self):
        user = make_user(MONDAY - timedelta(weeks=2) + timedelta(days=2))   # daftar hari Rabu 2 minggu lalu
        h = build_report_history(user, TODAY)
        self.assertEqual(
            [w['start'] for w in h['weeks']],
            [MONDAY - timedelta(weeks=1), MONDAY - timedelta(weeks=2)],     # terbaru dulu
        )
        self.assertEqual(h['joined'], MONDAY - timedelta(weeks=2) + timedelta(days=2))

    def test_weekly_totals_days_scans_and_over_budget_days(self):
        user = make_user(MONDAY - timedelta(weeks=1))
        last = MONDAY - timedelta(weeks=1)
        scan(user, last, 1200, raw='foto-1')            # hari 1: 1200 + 1000 = 2200 -> lewat budget
        scan(user, last, 1000, raw='foto-1')            # satu foto, dua item
        scan(user, last + timedelta(days=2), 600, raw='foto-2')   # hari 2: 600
        w = build_report_history(user, TODAY)['weeks'][0]
        self.assertEqual(w['total_kg'], 2.8)
        self.assertEqual(w['days_logged'], 2)
        self.assertEqual(w['scans'], 2)                 # 3 baris, tapi 2 foto
        self.assertEqual(w['over_days'], 1)
        self.assertEqual(w['avg_day_kg'], 1.4)

    def test_week_without_scans_is_listed_as_empty(self):
        user = make_user(MONDAY - timedelta(weeks=2))
        scan(user, MONDAY - timedelta(weeks=2), 700)
        weeks = build_report_history(user, TODAY)['weeks']
        self.assertFalse(weeks[0]['has_data'])          # minggu lalu: tidak scan
        self.assertTrue(weeks[1]['has_data'])

    def test_change_compares_with_previous_week_that_has_data(self):
        user = make_user(MONDAY - timedelta(weeks=3))
        scan(user, MONDAY - timedelta(weeks=3), 1000)
        # minggu -2 kosong
        scan(user, MONDAY - timedelta(weeks=1), 500)
        weeks = build_report_history(user, TODAY)['weeks']
        self.assertEqual(weeks[0]['delta_percent'], -50)     # 500 vs 1000
        self.assertIsNone(weeks[2]['delta_percent'])         # minggu pertama, tak ada pembanding

    def test_summary_average_projection_and_best_week(self):
        user = make_user(MONDAY - timedelta(weeks=2))
        scan(user, MONDAY - timedelta(weeks=2), 1000)        # 1,0 kg/hari
        scan(user, MONDAY - timedelta(weeks=1), 2000)        # 2,0 kg/hari
        h = build_report_history(user, TODAY)
        self.assertEqual(h['weeks_with_data'], 2)
        self.assertEqual(h['avg_day_kg'], 1.5)
        self.assertEqual(h['projection_kg'], round(1.5 * 365))
        self.assertEqual(h['best']['start'], MONDAY - timedelta(weeks=2))

    def test_history_is_limited_to_window(self):
        user = make_user(MONDAY - timedelta(weeks=REPORT_HISTORY_WEEKS + 10))
        weeks = build_report_history(user, TODAY)['weeks']
        self.assertEqual(len(weeks), REPORT_HISTORY_WEEKS)
        self.assertEqual(weeks[-1]['start'], MONDAY - timedelta(weeks=REPORT_HISTORY_WEEKS))

    def test_other_users_scans_are_not_included(self):
        user = make_user(MONDAY - timedelta(weeks=1))
        other = User.objects.create_user('lain', password='x12345678')
        scan(other, MONDAY - timedelta(weeks=1), 5000)
        self.assertFalse(build_report_history(user, TODAY)['weeks'][0]['has_data'])
