# =====================================================================================
# TEST API Django REST Framework modul Social (dipakai aplikasi mobile Flutter).
#
# Jalankan: python manage.py test social.test_api
# APIClient = "aplikasi palsu" dari DRF untuk mengirim request JSON ke endpoint.
# Pola tiap test tetap Arrange -> Act -> Assert (lihat penjelasan di tests.py).
# =====================================================================================
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import CampusMembership, Friendship, University
from .tests import scan


class ApiTestCase(TestCase):
    """Data dasar yang dipakai semua test API: 3 user, 2 kampus."""

    def setUp(self):
        cache.clear()  # kuota rate limit mulai dari nol
        self.client = APIClient()
        self.ui = University.objects.create(name='Universitas Indonesia', short_name='UI', city='Depok')
        self.itb = University.objects.create(name='Institut Teknologi Bandung', short_name='ITB', city='Bandung')
        self.iqbal = User.objects.create_user('iqbal', password='pass12345x')
        self.nami = User.objects.create_user('nami', password='pass12345x')
        self.acan = User.objects.create_user('acan', password='pass12345x')

    # Helper: GET / POST lalu kembalikan (status, json).
    def get(self, name, params=None, args=None):
        res = self.client.get(reverse(f'social:{name}', args=args), params or {})
        return res.status_code, res.json()

    def post(self, name, data=None, args=None):
        res = self.client.post(reverse(f'social:{name}', args=args), data or {}, format='json')
        return res.status_code, res.json()


class LeaderboardApiTests(ApiTestCase):
    def test_national_tab_for_guest(self):
        # Arrange: nami 300 g, iqbal 900 g, acan baru 2 scan (belum masuk peringkat).
        scan(self.nami, 300, times=3)
        scan(self.iqbal, 900, times=3)
        scan(self.acan, 100, times=2)
        CampusMembership.objects.create(user=self.nami, university=self.ui)
        # Act
        code, data = self.get('api_leaderboard')
        # Assert: urutan, bentuk JSON, dan tamu tidak punya baris "is_me".
        self.assertEqual(code, 200)
        self.assertEqual(data['tab'], 'national')
        self.assertEqual([(r['pos'], r['username'], r['avg_co2']) for r in data['results']],
                         [(1, 'nami', 300), (2, 'iqbal', 900)])
        self.assertEqual(data['results'][0]['campus'], 'UI')
        self.assertIsNone(data['results'][1]['campus'])
        self.assertEqual(data['min_scans'], 3)
        self.assertEqual([t['key'] for t in data['tabs']], ['friends', 'campus', 'national'])
        self.assertFalse(any(r['is_me'] for r in data['results']))

    def test_reasons_and_my_progress(self):
        # Tamu membuka tab kampus -> reason login; tab aneh -> national.
        self.assertEqual(self.get('api_leaderboard', {'tab': 'campus'})[1]['reason'], 'login')
        self.assertEqual(self.get('api_leaderboard', {'tab': 'galaksi'})[1]['tab'], 'national')
        # Login tanpa kampus & teman.
        self.client.force_authenticate(self.iqbal)
        scan(self.iqbal, 400)
        self.assertEqual(self.get('api_leaderboard', {'tab': 'campus'})[1]['reason'], 'campus')
        data = self.get('api_leaderboard')[1]       # tab nasional: baru 1 scan -> butuh 2 lagi
        self.assertEqual((data['my_scans'], data['scans_needed'], data['results']), (1, 2, []))
        self.assertEqual(self.get('api_leaderboard', {'tab': 'friends'})[1]['reason'], 'no_friends')

    def test_friends_tab_marks_my_row(self):
        Friendship.objects.create(from_user=self.iqbal, to_user=self.nami, status=Friendship.ACCEPTED)
        for user in (self.iqbal, self.nami, self.acan):
            scan(user, 500, times=3)
        self.client.force_authenticate(self.iqbal)
        data = self.get('api_leaderboard', {'tab': 'friends'})[1]
        self.assertEqual({r['username'] for r in data['results']}, {'iqbal', 'nami'})
        self.assertEqual([r['username'] for r in data['results'] if r['is_me']], ['iqbal'])


class CampusApiTests(ApiTestCase):
    def test_campus_war_and_universities(self):
        CampusMembership.objects.create(user=self.iqbal, university=self.ui)
        scan(self.iqbal, 300, times=3)
        code, data = self.get('api_campus_war')
        self.assertEqual(code, 200)
        self.assertIsNone(data['my_campus'])          # tamu
        first, second = data['results']
        self.assertEqual((first['short_name'], first['pos'], first['avg_co2']), ('UI', 1, 300))
        self.assertEqual((second['short_name'], second['pos'], second['avg_co2']), ('ITB', None, None))
        self.client.force_authenticate(self.iqbal)
        self.assertEqual(self.get('api_campus_war')[1]['my_campus']['short_name'], 'UI')
        self.assertEqual([u['short_name'] for u in self.get('api_universities')[1]], ['ITB', 'UI'])

    def test_choose_campus_create_update_and_errors(self):
        self.assertEqual(self.post('api_choose_campus', {'university': self.ui.pk})[0], 403)  # wajib login
        self.client.force_authenticate(self.iqbal)
        code, data = self.post('api_choose_campus', {'university': self.ui.pk})
        self.assertEqual((code, data['message'], data['campus']['short_name']), (200, 'Kampusmu sekarang UI.', 'UI'))
        self.post('api_choose_campus', {'university': self.itb.pk})
        self.assertEqual(CampusMembership.objects.get().university, self.itb)  # update, bukan baris baru
        self.assertEqual(self.post('api_choose_campus', {'university': 999}), (400, {'ok': False, 'message': 'Kampus tidak ditemukan.'}))
        self.assertEqual(self.post('api_choose_campus', {})[1]['message'], 'Pilih kampus dulu.')


class FriendApiTests(ApiTestCase):
    def test_requires_login(self):
        self.assertEqual(self.get('api_friends')[0], 403)
        self.assertEqual(self.post('api_friend_request', {'username': 'nami'})[0], 403)

    def test_full_flow_send_accept_list_unfriend(self):
        # Kirim
        self.client.force_authenticate(self.iqbal)
        code, data = self.post('api_friend_request', {'username': 'nami'})
        self.assertEqual((code, data['ok']), (200, True))
        pending = Friendship.objects.get()
        out = self.get('api_friends')[1]['outgoing']
        self.assertEqual((out[0]['id'], out[0]['user']['username']), (pending.pk, 'nami'))
        # Terima oleh nami
        self.client.force_authenticate(self.nami)
        incoming = self.get('api_friends')[1]['incoming']
        self.assertEqual(incoming[0]['user']['username'], 'iqbal')
        code, data = self.post('api_friend_respond', {'action': 'accept'}, args=[pending.pk])
        self.assertEqual((code, data['message']), (200, 'Kamu sekarang berteman dengan iqbal!'))
        # Daftar teman + pencarian
        friends = self.get('api_friends', {'q': 'a'})[1]
        self.assertEqual([(f['user']['username'], f['xp'], f['friendship_id']) for f in friends['friends']],
                         [('iqbal', 0, pending.pk)])
        self.assertEqual([(r['user']['username'], r['status']) for r in friends['results']],
                         [('acan', 'none'), ('iqbal', 'friends')])
        # Unfriend
        self.assertEqual(self.post('api_friend_delete', args=[pending.pk])[0], 200)
        self.assertFalse(Friendship.objects.exists())

    def test_validation_and_ownership_errors(self):
        self.client.force_authenticate(self.iqbal)
        self.assertEqual(self.post('api_friend_request', {'username': 'hantu'})[1]['message'], 'User "hantu" tidak ditemukan.')
        self.assertEqual(self.post('api_friend_request', {'username': 'iqbal'})[1]['message'],
                         'Kamu tidak bisa menambahkan dirimu sendiri.')
        self.assertEqual(self.post('api_friend_request', {})[1]['message'], 'Username wajib diisi.')
        self.post('api_friend_request', {'username': 'nami'})
        code, data = self.post('api_friend_request', {'username': 'nami'})            # dobel
        self.assertEqual((code, data['ok']), (400, False))
        f = Friendship.objects.get()
        self.assertEqual(self.post('api_friend_respond', {'action': 'accept'}, args=[f.pk])[0], 400)  # pengirim
        self.client.force_authenticate(self.nami)
        self.assertEqual(self.post('api_friend_respond', {'action': 'hapus'}, args=[f.pk])[1]['message'],
                         'Pilihan harus terima atau tolak.')
        self.client.force_authenticate(self.acan)
        self.assertEqual(self.post('api_friend_delete', args=[f.pk])[0], 400)          # orang luar
        self.assertEqual(self.post('api_friend_delete', args=[999])[0], 404)
        self.assertEqual(self.client.get(reverse('social:api_friend_request')).status_code, 405)

    def test_rate_limit(self):
        self.client.force_login(self.iqbal)
        for i in range(10):
            User.objects.create_user(f'teman{i}')
            self.post('api_friend_request', {'username': f'teman{i}'})
        code, data = self.post('api_friend_request', {'username': 'nami'})
        self.assertEqual((code, data['ok']), (429, False))


class MobileIntegrationTests(ApiTestCase):
    """Meniru aplikasi Flutter: login lewat session cookie, POST JSON tanpa token CSRF."""

    def test_session_cookie_post_without_csrf_token(self):
        client = APIClient(enforce_csrf_checks=True)   # cek CSRF aktif seperti server sungguhan
        client.force_login(self.iqbal)                 # menghasilkan cookie sessionid
        res = client.post(reverse('social:api_friend_request'), {'username': 'nami'}, format='json')
        self.assertEqual(res.status_code, 200)

    def test_web_form_still_requires_csrf(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.iqbal)
        res = client.post(reverse('social:friend_request_send'), {'username': 'nami'})
        self.assertEqual(res.status_code, 403)         # halaman web tetap terlindungi CSRF

    def test_cors_allows_flutter_web_on_localhost_only(self):
        url = reverse('social:api_leaderboard')
        res = self.client.get(url, HTTP_ORIGIN='http://localhost:54321')
        self.assertEqual(res['Access-Control-Allow-Origin'], 'http://localhost:54321')
        self.assertEqual(res['Access-Control-Allow-Credentials'], 'true')
        self.assertNotIn('Access-Control-Allow-Origin', self.client.get(url, HTTP_ORIGIN='https://jahat.example'))
