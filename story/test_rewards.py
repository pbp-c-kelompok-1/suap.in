from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from gamification.services import get_profile

from .models import MilestoneReward


class MilestoneRewardTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='reward-owner',
        )
        self.other = get_user_model().objects.create_user(
            username='reward-other',
        )
        self.profile = get_profile(self.user)
        self.client.force_login(self.user)
        self.list_url = reverse('story:reward_list')

    def unlock_reward(self):
        # siapkan akun yg baru mencapai milestone streak pertama
        self.profile.record_streak = 3
        self.profile.save(update_fields=['record_streak'])

        return MilestoneReward.objects.get(
            user=self.user,
            code='streak-3',
        )

    def test_new_account_has_seven_locked_milestones(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['cards']), 7)
        self.assertEqual(response.context['available_count'], 0)
        self.assertContains(response, 'Belum terbuka', count=7)

    def test_profile_save_creates_reward_without_duplicates(self):
        self.unlock_reward()
        self.profile.save(update_fields=['record_streak'])

        self.assertEqual(
            MilestoneReward.objects.filter(user=self.user).count(),
            1,
        )

    def test_old_progress_is_checked_when_opening_page(self):
        # update() melewati signal, jadi ini meniru progres akun lama
        type(self.profile).objects.filter(
            pk=self.profile.pk,
        ).update(record_streak=7)

        response = self.client.get(self.list_url)

        self.assertEqual(response.context['available_count'], 2)

    def test_ajax_claim_only_adds_xp_once(self):
        reward = self.unlock_reward()
        url = reverse('story:reward_claim', args=[reward.pk])

        first = self.client.post(
            url,
            HTTP_ACCEPT='application/json',
        )
        second = self.client.post(
            url,
            HTTP_ACCEPT='application/json',
        )

        self.assertTrue(first.json()['claimed'])
        self.assertFalse(second.json()['claimed'])
        self.assertIn('Sudah diklaim', first.json()['html'])

        self.profile.refresh_from_db()
        reward.refresh_from_db()

        self.assertEqual(self.profile.total_xp, 25)
        self.assertIsNotNone(reward.claimed_at)

    def test_another_account_cannot_claim_reward(self):
        reward = self.unlock_reward()
        self.client.force_login(self.other)

        response = self.client.post(
            reverse('story:reward_claim', args=[reward.pk]),
        )

        self.assertEqual(response.status_code, 404)

        reward.refresh_from_db()
        self.assertIsNone(reward.claimed_at)

    def test_claim_requires_post_and_csrf(self):
        reward = self.unlock_reward()
        url = reverse('story:reward_claim', args=[reward.pk])

        # Membuka URL dengan GET gk boleh langsung mengklaim hadiah
        self.assertEqual(self.client.get(url).status_code, 405)

        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)

        self.assertEqual(client.post(url).status_code, 403)

        # Ambil token dari halaman, lalu coba POST yang valid
        client.get(self.list_url)
        response = client.post(url, {
            'csrfmiddlewaretoken': client.cookies['csrftoken'].value,
        })

        self.assertEqual(response.status_code, 302)