import unittest
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from scanner.models import FoodLog
from story.models import FriendChallenge

from .duels import decline_duel, finalize_due_duels, has_lifecycle
from .models import ChallengeProfile, Notification


needs_story = unittest.skipUnless(
    has_lifecycle(), 'butuh app story dari master (terima, skor, dan hasil tantangan)'
)


def accept(user, pk):
    from story.challenge_services import accept_challenge
    return accept_challenge(user, pk)


def make_user(name):
    return User.objects.create_user(name, password='x12345678')


def log(user, when, grams=500):
    entry = FoodLog.objects.create(user=user, custom_name='x', co2_grams=grams)
    FoodLog.objects.filter(pk=entry.pk).update(scanned_at=when)


class DeclineDuelTests(TestCase):
    def setUp(self):
        self.a, self.b, self.c = make_user('a'), make_user('b'), make_user('c')
        self.ch = FriendChallenge.objects.create(challenger=self.a, opponent=self.b)

    def test_opponent_declines_challenge_is_removed_and_challenger_notified(self):
        decline_duel(self.b, self.ch.pk)
        self.assertFalse(FriendChallenge.objects.filter(pk=self.ch.pk).exists())
        n = Notification.objects.get(user=self.a, key=f'challenge-declined-{self.ch.pk}')
        self.assertEqual(n.title, 'b menolak tantanganmu')
        self.assertFalse(n.ephemeral)              # kabar ini tetap ada, tidak hilang sendiri
        self.assertEqual(n.link, reverse('story:challenge_list'))

    def test_notification_uses_display_name(self):
        ChallengeProfile.objects.create(user=self.b, display_name='Budi Hijau')
        decline_duel(self.b, self.ch.pk)
        self.assertEqual(Notification.objects.get(user=self.a).title, 'Budi Hijau menolak tantanganmu')

    def test_only_opponent_may_decline(self):
        for outsider in (self.a, self.c):
            with self.assertRaises(PermissionDenied):
                decline_duel(outsider, self.ch.pk)
        self.assertTrue(FriendChallenge.objects.filter(pk=self.ch.pk, status='pending').exists())
        self.assertFalse(Notification.objects.exists())

    @needs_story
    def test_cannot_decline_after_accept(self):
        accept(self.b, self.ch.pk)
        with self.assertRaises(ValidationError):
            decline_duel(self.b, self.ch.pk)
        self.ch.refresh_from_db()
        self.assertEqual(self.ch.status, 'active')

    def test_cannot_decline_twice(self):
        decline_duel(self.b, self.ch.pk)
        with self.assertRaises(FriendChallenge.DoesNotExist):
            decline_duel(self.b, self.ch.pk)

    def test_endpoint_permissions_and_responses(self):
        url = reverse('challenge:challenge_decline', args=[self.ch.pk])
        self.assertEqual(self.client.post(url).status_code, 302)             # belum login
        self.client.force_login(self.c)
        self.assertEqual(self.client.post(url).status_code, 403)
        self.client.force_login(self.b)
        self.assertEqual(self.client.get(url).status_code, 405)
        res = self.client.post(url)
        self.assertEqual((res.status_code, res.json()), (200, {'ok': True, 'message': 'Tantangan ditolak.'}))
        self.assertEqual(self.client.post(url).status_code, 404)             # sudah dihapus

    @needs_story
    def test_endpoint_conflict_when_already_accepted(self):
        accept(self.b, self.ch.pk)
        self.client.force_login(self.b)
        res = self.client.post(reverse('challenge:challenge_decline', args=[self.ch.pk]))
        self.assertEqual(res.status_code, 409)
        self.assertFalse(res.json()['ok'])

    def test_unknown_challenge_is_404(self):
        self.client.force_login(self.b)
        url = reverse('challenge:challenge_decline', args=['00000000-0000-0000-0000-000000000000'])
        self.assertEqual(self.client.post(url).status_code, 404)


@needs_story
class FinalizeDueDuelsTests(TestCase):
    def setUp(self):
        self.a, self.b = make_user('a'), make_user('b')
        self.now = timezone.now()
        self.start = self.now - timedelta(days=8)

    def duel(self, metric='lowest_co2', ends_in=-1):
        return FriendChallenge.objects.create(
            challenger=self.a, opponent=self.b, metric=metric, status='active',
            duration_days=7, started_at=self.start,
            ends_at=self.now + timedelta(days=ends_in),
        )

    def test_finishes_expired_duel_and_picks_lowest_co2_winner(self):
        ch = self.duel()
        log(self.a, self.start + timedelta(days=1), 300)
        log(self.b, self.start + timedelta(days=1), 900)
        done = finalize_due_duels(self.a, self.now)
        self.assertEqual([c.pk for c in done], [ch.pk])
        ch.refresh_from_db()
        self.assertEqual((ch.status, ch.winner_id), ('finished', self.a.pk))
        self.assertEqual(ch.result_snapshot['opponent']['co2'], 900)

    def test_most_scans_winner(self):
        ch = self.duel('most_scans')
        for i in range(3):
            log(self.b, self.start + timedelta(hours=i + 1), 800)
        log(self.a, self.start + timedelta(hours=1), 100)
        finalize_due_duels(self.b, self.now)
        ch.refresh_from_db()
        self.assertEqual(ch.winner_id, self.b.pk)

    def test_tie_has_no_winner(self):
        ch = self.duel()
        log(self.a, self.start + timedelta(hours=1), 500)
        log(self.b, self.start + timedelta(hours=2), 500)
        finalize_due_duels(self.a, self.now)
        ch.refresh_from_db()
        self.assertEqual((ch.status, ch.winner_id), ('finished', None))

    def test_participant_without_records_does_not_win_with_zero_emission(self):
        ch = self.duel()
        log(self.b, self.start + timedelta(hours=1), 5000)
        finalize_due_duels(self.a, self.now)
        ch.refresh_from_db()
        self.assertEqual(ch.winner_id, self.b.pk)

    def test_running_duel_is_left_alone(self):
        ch = self.duel(ends_in=2)
        self.assertEqual(finalize_due_duels(self.a, self.now), [])
        ch.refresh_from_db()
        self.assertEqual(ch.status, 'active')

    def test_idempotent_and_scores_stay_frozen(self):
        ch = self.duel()
        log(self.a, self.start + timedelta(hours=1), 200)
        log(self.b, self.start + timedelta(hours=1), 400)
        finalize_due_duels(self.a, self.now)
        FoodLog.objects.filter(user=self.b).delete()
        self.assertEqual(finalize_due_duels(self.a, self.now), [])
        ch.refresh_from_db()
        self.assertEqual(ch.result_snapshot['opponent']['co2'], 400)
        self.assertEqual(ch.winner_id, self.a.pk)

    def test_other_peoples_duels_are_not_touched(self):
        x, y = make_user('x'), make_user('y')
        other = FriendChallenge.objects.create(
            challenger=x, opponent=y, status='active',
            started_at=self.start, ends_at=self.now - timedelta(days=1),
        )
        finalize_due_duels(self.a, self.now)
        other.refresh_from_db()
        self.assertEqual(other.status, 'active')

    def test_logs_outside_the_window_do_not_count(self):
        ch = self.duel('most_scans')
        log(self.a, self.start - timedelta(hours=5))
        log(self.a, self.now - timedelta(hours=1))
        log(self.b, self.start + timedelta(hours=3))
        finalize_due_duels(self.a, self.now)
        ch.refresh_from_db()
        self.assertEqual(ch.winner_id, self.b.pk)
