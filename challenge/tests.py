from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from scanner.models import FoodLog
from social.models import CampusMembership, University


class ChallengeAuthGateTests(TestCase):
    def test_anonymous_redirected_to_login_with_next(self):
        for name in ('challenge:list', 'challenge:report', 'challenge:api_daily'):
            url = reverse(name)
            res = self.client.get(url)
            self.assertEqual(res.status_code, 302, name)
            self.assertIn(reverse('authentication:login'), res['Location'])
            self.assertIn('next=', res['Location'])

    def test_claim_freeze_requires_login_and_post(self):
        url = reverse('challenge:claim_freeze')
        self.assertEqual(self.client.post(url).status_code, 302)
        self.client.force_login(User.objects.create_user('a', password='x12345678'))
        self.assertEqual(self.client.get(url).status_code, 405)

    def test_claim_freeze_refused_when_quests_not_done(self):
        self.client.force_login(User.objects.create_user('a', password='x12345678'))
        res = self.client.post(reverse('challenge:claim_freeze'))
        self.assertEqual(res.status_code, 400)


class ChallengeDataTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('nami', password='x12345678')
        self.client.force_login(self.user)

    def data(self):
        return self.client.get(reverse('challenge:list')).context['challenge_data']

    def test_new_user_has_no_placeholder_data(self):
        d = self.data()
        self.assertEqual(d['totalScans'], 0)
        self.assertFalse(d['hasWeekData'])
        # Satu-satunya notifikasi untuk user baru: kabar 3 misi hari ini (tanpa lencana/rank palsu).
        self.assertEqual([n['id'][:10] for n in d['notifs']], ['quests-new'])
        self.assertEqual(d['rank']['teman']['empty'], 'no_friends')
        self.assertEqual(d['rank']['kampus']['empty'], 'no_campus')
        # Belum pernah scan: tidak ikut peringkat, diarahkan untuk scan dulu.
        self.assertEqual(d['rank']['nasional']['empty'], 'no_scan')
        self.assertEqual(d['rank']['nasional']['items'], [])
        self.assertEqual(d['weeklyRanking']['position'], None)

        self.assertEqual(d['stats']['campusRank'], None)
        self.assertTrue(all(q['val'] == 0 for q in d['quests']))
        
    def test_rank_uses_real_users_and_excludes_unscanned_users(self):
        other = User.objects.create_user('sinta', password='x12345678')
        User.objects.create_user('belum_scan', password='x12345678')
        for _ in range(3):
            FoodLog.objects.create(user=other, custom_name='Nasi', co2_grams=1500)
            FoodLog.objects.create(user=self.user, custom_name='Salad', co2_grams=300)
        rows = self.data()['rank']['nasional']['items']
        self.assertEqual([r['name'] for r in rows], ['nami', 'sinta'])
        self.assertEqual([r['pos'] for r in rows], [1, 2])

    def test_campus_rank_and_my_position(self):
        uni = University.objects.create(name='Universitas Indonesia', short_name='UI')
        other = User.objects.create_user('sinta', password='x12345678')
        for u in (self.user, other):
            CampusMembership.objects.create(user=u, university=uni)
        for _ in range(3):
            FoodLog.objects.create(user=other, custom_name='Nasi', co2_grams=1000)
            FoodLog.objects.create(user=self.user, custom_name='Rendang', co2_grams=4000)
        d = self.data()
        self.assertEqual([r['name'] for r in d['rank']['kampus']['items']], ['sinta', 'nami'])
        self.assertEqual(d['stats']['campusRank'], 2)
        self.assertEqual(d['totalScans'], 3)
