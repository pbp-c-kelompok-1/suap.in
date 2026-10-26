from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import FriendChallenge


class ChallengeViewTests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.sender = User.objects.create_user(
            username='pengirim-view',
        )
        self.receiver = User.objects.create_user(
            username='penerima-view',
        )
        self.other = User.objects.create_user(
            username='akun-lain-view',
        )

        self.challenge = FriendChallenge.objects.create(
            challenger=self.sender,
            opponent=self.receiver,
            duration_days=3,
        )

        self.list_url = reverse('story:challenge_list')
        self.accept_url = reverse(
            'story:challenge_accept',
            args=[self.challenge.pk],
        )
        self.cancel_url = reverse(
            'story:cancel_challenge',
            args=[self.challenge.pk],
        )
        self.refresh_url = reverse(
            'story:challenge_refresh',
            args=[self.challenge.pk],
        )

        self.client.force_login(self.sender)

    def test_guest_must_login(self):
        self.client.logout()

        self.assertEqual(
            self.client.get(self.list_url).status_code,
            302,
        )
        self.assertEqual(
            self.client.post(self.accept_url).status_code,
            302,
        )

    def test_sender_is_taken_from_logged_in_account(self):
        response = self.client.post(self.list_url, {
            'opponent': self.receiver.pk,
            'metric': 'most_scans',
            'duration_days': 7,

            # Coba kirim pengirim palsu; server harus tetap pakai akun login.
            'challenger': self.other.pk,
        })

        self.assertRedirects(response, self.list_url)

        newest = FriendChallenge.objects.first()

        self.assertEqual(newest.challenger_id, self.sender.pk)
        self.assertEqual(newest.status, 'pending')

    def test_invalid_opponent_does_not_create_challenge(self):
        response = self.client.post(self.list_url, {
            'opponent': self.sender.pk,
            'metric': 'most_scans',
            'duration_days': 3,
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn('opponent', response.context['form'].errors)
        self.assertEqual(FriendChallenge.objects.count(), 1)

    def test_list_only_contains_own_challenges(self):
        self.client.force_login(self.other)

        response = self.client.get(self.list_url)

        self.assertEqual(response.context['cards'], [])
        self.assertContains(response, 'Belum ada tantangan')

    def test_receiver_accepts_with_post(self):
        self.client.force_login(self.receiver)

        self.assertEqual(
            self.client.get(self.accept_url).status_code,
            405,
        )

        response = self.client.post(
            self.accept_url,
            HTTP_ACCEPT='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('Berlangsung', response.json()['html'])

        self.challenge.refresh_from_db()
        self.assertEqual(self.challenge.status, 'active')

    def test_nonreceiver_cannot_accept(self):
        for user in [self.sender, self.other]:
            self.client.force_login(user)

            self.assertEqual(
                self.client.post(self.accept_url).status_code,
                403,
            )

        self.challenge.refresh_from_db()
        self.assertEqual(self.challenge.status, 'pending')

    def test_sender_can_cancel_pending_challenge(self):
        response = self.client.post(
            self.cancel_url,
            HTTP_ACCEPT='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            FriendChallenge.objects.filter(
                pk=self.challenge.pk,
            ).exists()
        )
        self.assertIn(
            'Belum ada tantangan',
            response.json()['html'],
        )

    def test_active_challenge_cannot_be_cancelled(self):
        self.client.force_login(self.receiver)
        self.client.post(self.accept_url)

        self.client.force_login(self.sender)

        self.assertEqual(
            self.client.post(self.cancel_url).status_code,
            404,
        )
        self.assertTrue(
            FriendChallenge.objects.filter(
                pk=self.challenge.pk,
            ).exists()
        )

    def test_refresh_finalizes_expired_challenge(self):
        FriendChallenge.objects.filter(
            pk=self.challenge.pk,
        ).update(
            status='active',
            started_at=timezone.now() - timedelta(days=4),
            ends_at=timezone.now() - timedelta(days=1),
        )

        response = self.client.post(
            self.refresh_url,
            HTTP_ACCEPT='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('Hasil seri', response.json()['html'])

        self.challenge.refresh_from_db()
        self.assertEqual(self.challenge.status, 'finished')

    def test_actions_require_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.receiver)

        for url in [
            self.accept_url,
            self.refresh_url,
            self.cancel_url,
        ]:
            with self.subTest(url=url):
                self.assertEqual(
                    client.post(url).status_code,
                    403,
                )