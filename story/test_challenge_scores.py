from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.utils import timezone

from scanner.models import FoodLog

from .challenge_services import (
    get_challenge_scores,
    refresh_challenge,
)
from .models import FriendChallenge


class ChallengeScoreTests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.left = User.objects.create_user(
            username='peserta-kiri',
        )
        self.right = User.objects.create_user(
            username='peserta-kanan',
        )
        self.other = User.objects.create_user(
            username='bukan-peserta',
        )

        # Periode sengaja dibuat sudah lewat supaya bisa menguji hasil akhir.
        self.start = timezone.now() - timedelta(days=4)
        self.end = self.start + timedelta(days=3)

        self.challenge = FriendChallenge.objects.create(
            challenger=self.left,
            opponent=self.right,
            metric='most_scans',
            status='active',
            duration_days=3,
            started_at=self.start,
            ends_at=self.end,
        )

    def log(self, user, co2=100, at=None):
        item = FoodLog.objects.create(
            user=user,
            custom_name='Makanan uji',
            co2_grams=co2,
        )

        # auto_now_add selalu mengisi waktu sekarang.
        # Untuk tes, waktunya diganti sesuai skenario yang mau diperiksa.
        FoodLog.objects.filter(pk=item.pk).update(
            scanned_at=(
                at
                if at is not None
                else self.start + timedelta(hours=1)
            ),
        )

        return item

    def test_only_participants_and_period_are_counted(self):
        self.log(
            self.left,
            at=self.start - timedelta(seconds=1),
        )
        self.log(self.left, at=self.start)
        self.log(self.left, at=self.end)
        self.log(self.other)

        scores = get_challenge_scores(
            self.challenge,
            now=self.end,
        )

        self.assertEqual(scores['challenger']['count'], 1)
        self.assertEqual(scores['challenger']['co2'], 100)
        self.assertEqual(scores['opponent']['count'], 0)

    def test_challenge_is_not_finished_early(self):
        _, scores = refresh_challenge(
            self.left,
            self.challenge.pk,
            now=self.start + timedelta(minutes=30),
        )

        self.challenge.refresh_from_db()

        self.assertEqual(self.challenge.status, 'active')
        self.assertIsNone(self.challenge.finished_at)
        self.assertEqual(scores['challenger']['count'], 0)

    def test_most_records_wins(self):
        self.log(self.left)
        self.log(self.left)
        self.log(self.right)

        challenge, _ = refresh_challenge(
            self.left,
            self.challenge.pk,
            now=self.end,
        )

        self.assertEqual(challenge.status, 'finished')
        self.assertEqual(challenge.winner_id, self.left.pk)

    def test_lower_total_co2_wins(self):
        self.challenge.metric = 'lowest_co2'
        self.challenge.save(update_fields=['metric'])

        self.log(self.left, co2=100)
        self.log(self.right, co2=200)

        challenge, _ = refresh_challenge(
            self.right,
            self.challenge.pk,
            now=self.end,
        )

        self.assertEqual(challenge.winner_id, self.left.pk)

    def test_no_records_does_not_win_lowest_co2(self):
        self.challenge.metric = 'lowest_co2'
        self.challenge.save(update_fields=['metric'])

        self.log(self.right, co2=200)

        challenge, _ = refresh_challenge(
            self.left,
            self.challenge.pk,
            now=self.end,
        )

        self.assertEqual(challenge.winner_id, self.right.pk)

    def test_both_empty_is_draw(self):
        challenge, _ = refresh_challenge(
            self.left,
            self.challenge.pk,
            now=self.end,
        )

        self.assertEqual(challenge.status, 'finished')
        self.assertIsNone(challenge.winner_id)

    def test_equal_scores_is_draw(self):
        self.log(self.left)
        self.log(self.right)

        challenge, _ = refresh_challenge(
            self.left,
            self.challenge.pk,
            now=self.end,
        )

        self.assertIsNone(challenge.winner_id)

    def test_finished_scores_survive_log_deletion(self):
        self.log(self.left)

        first, scores = refresh_challenge(
            self.left,
            self.challenge.pk,
            now=self.end,
        )

        FoodLog.objects.all().delete()

        again, saved = refresh_challenge(
            self.left,
            self.challenge.pk,
            now=self.end + timedelta(days=1),
        )

        self.assertEqual(saved, scores)
        self.assertEqual(again.winner_id, first.winner_id)
        self.assertEqual(again.finished_at, first.finished_at)

    def test_nonparticipant_cannot_finalize_challenge(self):
        with self.assertRaises(PermissionDenied):
            refresh_challenge(
                self.other,
                self.challenge.pk,
                now=self.end,
            )

        self.challenge.refresh_from_db()

        self.assertEqual(self.challenge.status, 'active')