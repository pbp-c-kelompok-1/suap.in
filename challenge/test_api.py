from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from .models import Notification


class ChallengeAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('annisa', password='pw12345')
        self.other = User.objects.create_user('lain', password='pw12345')

    def test_wajib_login(self):
        res = self.client.get('/api/challenge/daily/')
        self.assertIn(res.status_code, (401, 403))

    def test_daily_quests(self):
        self.client.force_authenticate(self.user)
        res = self.client.get('/api/challenge/daily/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('quests', res.data)

    def test_notifikasi_hanya_milik_sendiri(self):
        Notification.objects.create(user=self.user, key='a', kind='x', title='Punyaku')
        Notification.objects.create(user=self.other, key='b', kind='x', title='Punya orang')
        self.client.force_authenticate(self.user)
        res = self.client.get('/api/challenge/notifications/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual([n['title'] for n in res.data], ['Punyaku'])

    def test_hapus_notifikasi_jadi_dismissed(self):
        n = Notification.objects.create(user=self.user, key='a', kind='x', title='Hapus aku')
        self.client.force_authenticate(self.user)
        res = self.client.delete(f'/api/challenge/notifications/{n.pk}/')
        self.assertEqual(res.status_code, 204)
        n.refresh_from_db()
        self.assertTrue(n.dismissed)

    def test_tandai_dibaca(self):
        n = Notification.objects.create(user=self.user, key='a', kind='x', title='Baca aku')
        self.client.force_authenticate(self.user)
        res = self.client.post(f'/api/challenge/notifications/{n.pk}/read/')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data['is_read'])
