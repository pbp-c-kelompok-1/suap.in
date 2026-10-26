from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from .challenge_services import accept_challenge
from .forms import FriendChallengeForm
from .models import FriendChallenge


class FriendChallengeTests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.sender = User.objects.create_user(
            username='pengirim',
        )
        self.opponent = User.objects.create_user(
            username='penerima',
        )
        self.other = User.objects.create_user(
            username='akun-lain',
        )
        self.inactive = User.objects.create_user(
            username='nonaktif',
            is_active=False,
        )

        self.challenge = FriendChallenge.objects.create(
            challenger=self.sender,
            opponent=self.opponent,
            duration_days=3,
        )

    def test_receiver_can_start_challenge(self):
        challenge = accept_challenge(
            self.opponent,
            self.challenge.pk,
        )

        self.assertEqual(challenge.status, 'active')
        self.assertIsNotNone(challenge.started_at)
        self.assertEqual(
            challenge.ends_at - challenge.started_at,
            timedelta(days=3),
        )
        self.assertIsNone(challenge.finished_at)

    def test_other_accounts_cannot_accept(self):
        # coba pake akun pengirim dan akun yang ga ikut tantangan
        for user in [self.sender, self.other]:
            with self.subTest(user=user.username):
                with self.assertRaises(PermissionDenied):
                    accept_challenge(user, self.challenge.pk)

        self.challenge.refresh_from_db()

        self.assertEqual(self.challenge.status, 'pending')
        self.assertIsNone(self.challenge.started_at)

    def test_accepting_twice_does_not_restart_timer(self):
        first = accept_challenge(
            self.opponent,
            self.challenge.pk,
        )

        with self.assertRaises(ValidationError):
            accept_challenge(self.opponent, self.challenge.pk)

        self.challenge.refresh_from_db()

        self.assertEqual(
            self.challenge.started_at,
            first.started_at,
        )
        self.assertEqual(
            self.challenge.ends_at,
            first.ends_at,
        )

    def test_form_rejects_self_and_inactive_account(self):
        for opponent in [self.sender, self.inactive]:
            with self.subTest(opponent=opponent.username):
                form = FriendChallengeForm(
                    {
                        'opponent': opponent.pk,
                        'metric': 'most_scans',
                        'duration_days': 3,
                    },
                    user=self.sender,
                )

                self.assertFalse(form.is_valid())
                self.assertIn('opponent', form.errors)

    def test_form_accepts_active_opponent(self):
        form = FriendChallengeForm(
            {
                'opponent': self.opponent.pk,
                'metric': 'most_scans',
                'duration_days': 7,
            },
            user=self.sender,
        )

        self.assertTrue(form.is_valid(), form.errors)