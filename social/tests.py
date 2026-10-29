import io
import os
from pathlib import Path
import shutil
import tempfile
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from .friends import friends_of
from .models import Canteen, CommunityPost, Friendship, University


def tiny_photo():
    buf = io.BytesIO()
    Image.new('RGB', (4, 4), 'green').save(buf, format='JPEG')
    return SimpleUploadedFile('makan.jpg', buf.getvalue(), content_type='image/jpeg')


TEST_MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class CommunityMapTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user('nami', password='pass12345x')
        ui = University.objects.create(name='Universitas Indonesia', short_name='UI', city='Depok')
        self.kancil = Canteen.objects.create(name='Kancil', faculty='Fasilkom', university=ui,
                                             latitude='-6.370254', longitude='106.827638')
        self.kantek = Canteen.objects.create(name='Kantek', faculty='Teknik', university=ui,
                                             latitude='-6.363214', longitude='106.824636')

    def post(self, canteen, co2, **extra):
        data = {'user': self.user, 'photo': tiny_photo(), 'canteen': canteen,
                'total_co2_grams': co2, 'is_shared': True}
        data.update(extra)
        return CommunityPost.objects.create(**data)

    def pins(self, **params):
        res = self.client.get(reverse('social:api_canteens'), params)
        self.assertEqual(res.status_code, 200)
        return {p['name']: p for p in res.json()['canteens']}

    def test_map_page_open_for_guest(self):
        res = self.client.get(reverse('social:community_map'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'communityMap')

    def test_counts_only_shared_and_visible_posts(self):
        self.post(self.kancil, 400)
        self.post(self.kancil, 800)
        self.post(self.kancil, 9999, is_shared=False)
        self.post(self.kancil, 9999, is_hidden=True)
        pins = self.pins()
        self.assertEqual(pins['Kancil']['post_count'], 2)
        self.assertEqual(pins['Kancil']['avg_co2'], 600)
        self.assertEqual(pins['Kancil']['status'], 'green')
        self.assertEqual(pins['Kantek']['post_count'], 0)
        self.assertEqual(pins['Kantek']['status'], 'none')

    def test_range_filter(self):
        old = self.post(self.kancil, 500)
        CommunityPost.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=3))
        self.post(self.kancil, 500)
        self.assertEqual(self.pins(range='today')['Kancil']['post_count'], 1)
        self.assertEqual(self.pins(range='week')['Kancil']['post_count'], 2)
        self.assertEqual(self.pins(range='all')['Kancil']['post_count'], 2)

    def test_faculty_filter(self):
        pins = self.pins(faculty='Teknik')
        self.assertEqual(list(pins), ['Kantek'])

    def test_high_co2_is_red(self):
        self.post(self.kantek, 2500)
        self.assertEqual(self.pins()['Kantek']['status'], 'red')


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class CanteenPanelTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user('nami', password='pass12345x')
        ui = University.objects.create(name='Universitas Indonesia', short_name='UI', city='Depok')
        self.kancil = Canteen.objects.create(name='Kancil', faculty='Fasilkom', university=ui,
                                             latitude='-6.370254', longitude='106.827638')

    def post(self, **extra):
        data = {'user': self.user, 'photo': tiny_photo(), 'canteen': self.kancil,
                'total_co2_grams': 500, 'is_shared': True}
        data.update(extra)
        return CommunityPost.objects.create(**data)

    def get(self, **params):
        url = reverse('social:api_canteen_posts', args=[self.kancil.pk])
        res = self.client.get(url, params)
        self.assertEqual(res.status_code, 200)
        return res.json()

    def test_panel_summary_and_post_fields(self):
        self.post(food_name='Nasi ayam', price=15000, total_co2_grams=900)
        self.post(food_name='Gado-gado', price=12000, total_co2_grams=300)
        self.post(food_name='Rahasia', is_shared=False)
        data = self.get()
        self.assertEqual(data['canteen']['name'], 'Kancil')
        self.assertEqual(data['summary'], {'post_count': 2, 'avg_co2': 600, 'avg_price': 13500})
        newest = data['posts'][0]
        self.assertEqual(newest['food_name'], 'Gado-gado')
        self.assertEqual(newest['username'], 'nami')
        self.assertEqual(newest['status'], 'green')
        self.assertTrue(newest['photo_url'])

    def test_pagination(self):
        for _ in range(21):
            self.post()
        first = self.get()
        self.assertEqual(len(first['posts']), 20)
        self.assertTrue(first['has_more'])
        second = self.get(page=2)
        self.assertEqual(len(second['posts']), 1)
        self.assertFalse(second['has_more'])

    def test_inactive_canteen_is_404(self):
        self.kancil.is_active = False
        self.kancil.save()
        url = reverse('social:api_canteen_posts', args=[self.kancil.pk])
        self.assertEqual(self.client.get(url).status_code, 404)


class NearestCanteenTests(TestCase):
    """Aturan rekomendasi lokasi di PRD (radius, akurasi GPS, kantin berdekatan)."""

    def setUp(self):
        ui = University.objects.create(name='Universitas Indonesia', short_name='UI', city='Depok')
        make = lambda n, f, lat, lng: Canteen.objects.create(name=n, faculty=f, university=ui, latitude=lat, longitude=lng)
        self.kancil = make('Kancil', 'Fasilkom', '-6.370254', '106.827638')
        self.dallas = make('Dallas', 'FMIPA', '-6.369713', '106.827477')
        self.kantek = make('Kantek', 'Teknik', '-6.363214', '106.824636')

    def ask(self, lat, lng, accuracy=20):
        res = self.client.post(reverse('social:api_nearest'), {'lat': lat, 'lng': lng, 'accuracy': accuracy})
        self.assertEqual(res.status_code, 200)
        return res.json()

    def test_recommends_canteen_when_standing_on_it(self):
        data = self.ask(-6.363214, 106.824636)
        self.assertEqual(data['recommended'], self.kantek.id)
        self.assertEqual(data['candidates'][0]['name'], 'Kantek')

    def test_close_pair_is_ambiguous(self):
        # titik tengah Kancil-Dallas: selisih jarak keduanya < 30 m
        data = self.ask(-6.3699835, 106.8275575)
        self.assertIsNone(data['recommended'])
        self.assertEqual(data['reason'], 'ambiguous')

    def test_far_from_any_canteen(self):
        data = self.ask(-6.40, 106.80)
        self.assertIsNone(data['recommended'])
        self.assertEqual(data['reason'], 'far')

    def test_inaccurate_gps_gives_no_recommendation(self):
        data = self.ask(-6.363214, 106.824636, accuracy=500)
        self.assertEqual(data['reason'], 'inaccurate')

    def test_bad_input(self):
        res = self.client.post(reverse('social:api_nearest'), {'lat': 'abc', 'lng': '1'})
        self.assertEqual(res.status_code, 400)


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class ShareFromScanTests(TestCase):
    """Alur Scanner -> Community lewat halaman hasil scan."""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        import base64
        self.user = User.objects.create_user('nami', password='pass12345x')
        self.client.login(username='nami', password='pass12345x')
        ui = University.objects.create(name='Universitas Indonesia', short_name='UI', city='Depok')
        self.kancil = Canteen.objects.create(name='Kancil', faculty='Fasilkom', university=ui,
                                             latitude='-6.370254', longitude='106.827638')
        buf = io.BytesIO()
        Image.new('RGB', (2000, 1500), 'orange').save(buf, format='JPEG')
        session = self.client.session
        session['scan_result'] = {'detected_items': [{'name': 'Nasi putih', 'co2_grams': 240},
                                                     {'name': 'Ayam goreng', 'co2_grams': 890}]}
        session['scan_photo'] = 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()
        session.save()

    def save(self, **fields):
        return self.client.post(reverse('scanner:save_log'), fields)

    def test_result_page_shows_share_form(self):
        res = self.client.get(reverse('scanner:result'))
        self.assertContains(res, 'Bagikan ke Community')
        self.assertContains(res, 'value="Nasi putih, Ayam goreng"')
        self.assertContains(res, 'Kancil')

    def test_not_shared_by_default(self):
        self.save()
        self.assertEqual(CommunityPost.objects.count(), 0)

    def test_share_creates_post(self):
        self.save(community_share='1', community_canteen=str(self.kancil.id),
                  community_food_name='Nasi ayam', community_price='15000')
        post = CommunityPost.objects.get()
        self.assertEqual(post.canteen, self.kancil)
        self.assertEqual(post.food_name, 'Nasi ayam')
        self.assertEqual(post.price, 15000)
        self.assertEqual(post.total_co2_grams, 1130)
        self.assertTrue(post.is_shared)
        self.assertEqual(post.food_logs.count(), 2)
        with Image.open(post.photo.path) as img:
            self.assertLessEqual(max(img.size), 1080)

    def test_custom_location_and_defaults(self):
        self.save(community_share='1', community_canteen='other',
                  community_custom_location='Warung dekat kos', community_food_name='', community_price='abc')
        post = CommunityPost.objects.get()
        self.assertIsNone(post.canteen)
        self.assertEqual(post.custom_location, 'Warung dekat kos')
        self.assertEqual(post.food_name, 'Nasi putih, Ayam goreng')
        self.assertIsNone(post.price)


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class SeedShowcaseTests(TestCase):
    """Data awal showcase: foto dari static, aman dijalankan berkali-kali."""

    def setUp(self):
        import json
        from unittest import mock
        from social import seed

        self.tmp = tempfile.mkdtemp()
        photos = os.path.join(self.tmp, 'photos')
        os.makedirs(photos)
        Image.new('RGB', (10, 10), 'red').save(os.path.join(photos, 'kancil_1.jpg'))
        entries = [
            {'photo': 'kancil_1.jpg', 'canteen': 'Kancil', 'food_name': 'Gado-gado', 'price': 12000, 'co2_grams': 320},
            {'photo': 'kancil_1.jpg', 'canteen': 'Kantek', 'food_name': 'Gado-gado', 'price': 12000, 'co2_grams': 320},
            {'photo': 'tidak_ada.jpg', 'canteen': 'Kancil', 'food_name': 'Hilang'},
        ]
        json_path = os.path.join(self.tmp, 'seed.json')
        with open(json_path, 'w') as f:
            json.dump(entries, f)
        self.patches = [mock.patch.object(seed, 'STATIC_SEED_DIR', Path(photos)),
                        mock.patch.object(seed, 'SEED_JSON', Path(json_path))]
        for p in self.patches:
            p.start()
        seed.ensure_canteens(University, Canteen, log=lambda *a: None)
        self.seed = seed

    def tearDown(self):
        for p in self.patches:
            p.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_seed(self):
        return self.seed.seed_community_posts(User, Canteen, CommunityPost, log=lambda *a: None)

    def test_fixtures_loaded_and_seed_is_idempotent(self):
        self.assertEqual(Canteen.objects.count(), 6)
        self.assertEqual(self.run_seed(), 2)  # foto yang sama dipakai di 2 kantin
        self.assertEqual(self.run_seed(), 0)
        post = CommunityPost.objects.get(canteen__name='Kancil')
        self.assertEqual(post.user.username, 'tim.suapin')
        self.assertFalse(post.user.has_usable_password())
        self.assertTrue(post.is_shared)

    def test_seed_photo_served_from_static(self):
        self.run_seed()
        kancil = Canteen.objects.get(name='Kancil')
        data = self.client.get(reverse('social:api_canteen_posts', args=[kancil.pk]), {'range': 'all'}).json()
        self.assertEqual(data['posts'][0]['photo_url'], '/static/social/seed/kancil_1.jpg')


class FriendshipTests(TestCase):
    """CRUD Friendship sesuai README: kirim, lihat, terima/tolak, unfriend."""

    def setUp(self):
        self.iqbal = User.objects.create_user('iqbal', password='pass12345x')
        self.nami = User.objects.create_user('nami', password='pass12345x')
        self.acan = User.objects.create_user('acan', password='pass12345x')

    def login(self, user):
        self.client.force_login(user)

    def send(self, username, ajax=True):
        headers = {'HTTP_X_REQUESTED_WITH': 'fetch'} if ajax else {}
        return self.client.post(reverse('social:friend_request_send'), {'username': username}, **headers)

    def act(self, name, pk, **data):
        return self.client.post(reverse(f'social:{name}', args=[pk]), data, HTTP_X_REQUESTED_WITH='fetch')

    def test_friends_page_requires_login(self):
        res = self.client.get(reverse('social:friends'))
        self.assertEqual(res.status_code, 302)

    def test_send_and_accept_request(self):
        self.login(self.iqbal)
        res = self.send('nami')
        self.assertTrue(res.json()['ok'])
        f = Friendship.objects.get()
        self.assertEqual((f.from_user, f.to_user, f.status), (self.iqbal, self.nami, Friendship.PENDING))

        self.login(self.nami)
        res = self.act('friend_request_respond', f.pk, action='accept')
        self.assertTrue(res.json()['ok'])
        f.refresh_from_db()
        self.assertEqual(f.status, Friendship.ACCEPTED)
        self.assertEqual(set(friends_of(self.iqbal)), {self.nami})
        self.assertEqual(set(friends_of(self.nami)), {self.iqbal})

    def test_cannot_add_self_or_duplicate(self):
        self.login(self.iqbal)
        self.assertEqual(self.send('iqbal').status_code, 400)
        self.send('nami')
        res = self.send('nami')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(Friendship.objects.count(), 1)

    def test_reverse_request_auto_accepts(self):
        self.login(self.iqbal)
        self.send('nami')
        self.login(self.nami)
        self.send('iqbal')
        self.assertEqual(Friendship.objects.get().status, Friendship.ACCEPTED)

    def test_only_receiver_can_respond(self):
        self.login(self.iqbal)
        self.send('nami')
        f = Friendship.objects.get()
        res = self.act('friend_request_respond', f.pk, action='accept')  # pengirim mencoba menerima sendiri
        self.assertEqual(res.status_code, 400)
        self.login(self.acan)
        self.assertEqual(self.act('friend_request_respond', f.pk, action='accept').status_code, 400)

    def test_reject_then_send_again(self):
        self.login(self.iqbal)
        self.send('nami')
        f = Friendship.objects.get()
        self.login(self.nami)
        self.act('friend_request_respond', f.pk, action='reject')
        f.refresh_from_db()
        self.assertEqual(f.status, Friendship.REJECTED)
        self.login(self.iqbal)
        self.assertTrue(self.send('nami').json()['ok'])
        f.refresh_from_db()
        self.assertEqual(f.status, Friendship.PENDING)

    def test_cancel_and_unfriend(self):
        self.login(self.iqbal)
        self.send('nami')
        f = Friendship.objects.get()
        self.login(self.nami)  # penerima tidak bisa "membatalkan", harus menolak
        self.assertEqual(self.act('friendship_delete', f.pk).status_code, 400)
        self.login(self.iqbal)
        self.assertTrue(self.act('friendship_delete', f.pk).json()['ok'])
        self.assertFalse(Friendship.objects.exists())

        f = Friendship.objects.create(from_user=self.iqbal, to_user=self.nami, status=Friendship.ACCEPTED)
        self.login(self.nami)
        self.assertTrue(self.act('friendship_delete', f.pk).json()['ok'])
        self.assertEqual(list(friends_of(self.iqbal)), [])

    def test_outsider_cannot_delete(self):
        f = Friendship.objects.create(from_user=self.iqbal, to_user=self.nami, status=Friendship.ACCEPTED)
        self.login(self.acan)
        self.assertEqual(self.act('friendship_delete', f.pk).status_code, 400)
        self.assertTrue(Friendship.objects.exists())

    def test_page_lists_search_requests_and_friends(self):
        Friendship.objects.create(from_user=self.acan, to_user=self.iqbal)  # masuk
        Friendship.objects.create(from_user=self.iqbal, to_user=self.nami, status=Friendship.ACCEPTED)
        self.login(self.iqbal)
        res = self.client.get(reverse('social:friends'), {'q': 'a'})
        self.assertEqual([r['user'].username for r in res.context['results']], ['acan', 'nami'])
        self.assertEqual([r['status'] for r in res.context['results']], ['received', 'friends'])
        self.assertEqual([f.from_user for f in res.context['incoming']], [self.acan])
        self.assertEqual([row['user'] for row in res.context['friends']], [self.nami])
        partial = self.client.get(reverse('social:friends'), {'partial': '1'})
        self.assertNotContains(partial, '<html')

    def test_non_ajax_form_redirects_with_message(self):
        self.login(self.iqbal)
        res = self.send('nami', ajax=False)
        self.assertRedirects(res, reverse('social:friends'))

    def test_leaderboard_friends_tab(self):
        from gamification.services import award_xp
        Friendship.objects.create(from_user=self.iqbal, to_user=self.nami, status=Friendship.ACCEPTED)
        for u in (self.iqbal, self.nami, self.acan):
            award_xp(u, 20)
        self.login(self.iqbal)
        res = self.client.get(reverse('social:leaderboard'), {'tab': 'friends'})
        self.assertEqual({u.username for u in res.context['ranking']}, {'iqbal', 'nami'})

        self.login(self.acan)
        res = self.client.get(reverse('social:leaderboard'), {'tab': 'friends'})
        self.assertTrue(res.context['no_friends'])


class SidebarFriendsLinkTests(TestCase):
    def test_sidebar_has_friends_link_marked_active(self):
        user = User.objects.create_user('iqbal', password='pass12345x')
        self.client.force_login(user)
        res = self.client.get(reverse('social:friends'))
        self.assertContains(res, f'href="{reverse("social:friends")}" aria-current="page"')


class XPLeaderboardTests(TestCase):
    """Dua leaderboard, satu sumber XP: sepanjang waktu (social) dan mingguan (challenge)."""

    def setUp(self):
        from gamification.services import award_xp
        self.award = award_xp
        self.ui = University.objects.create(name='Universitas Indonesia', short_name='UI', city='Depok')
        self.itb = University.objects.create(name='Institut Teknologi Bandung', short_name='ITB', city='Bandung')
        self.iqbal = User.objects.create_user('iqbal', password='pass12345x')
        self.nami = User.objects.create_user('nami', password='pass12345x')
        self.acan = User.objects.create_user('acan', password='pass12345x')
        from .models import CampusMembership
        CampusMembership.objects.create(user=self.iqbal, university=self.ui)
        CampusMembership.objects.create(user=self.nami, university=self.ui)
        CampusMembership.objects.create(user=self.acan, university=self.itb)

    def age(self, user, days):
        """Geser semua XP user ke `days` hari yang lalu."""
        from .models import XPActivity
        XPActivity.objects.filter(user=user).update(created_at=timezone.now() - timedelta(days=days))

    def test_xp_gain_is_logged_from_gamification(self):
        from .models import XPActivity
        from gamification.services import get_profile
        get_profile(self.iqbal)  # profil baru, 0 XP: tidak dicatat
        self.award(self.iqbal, 15)
        self.award(self.iqbal, 11)
        self.assertEqual(list(XPActivity.objects.filter(user=self.iqbal).values_list('amount', flat=True).order_by('id')), [15, 11])

    def test_all_time_leaderboard_uses_total_xp(self):
        self.award(self.nami, 300)
        self.age(self.nami, 60)  # XP lama tetap dihitung di sepanjang waktu
        self.award(self.iqbal, 100)
        res = self.client.get(reverse('social:leaderboard'))
        self.assertEqual([(u.username, u.xp) for u in res.context['ranking']], [('nami', 300), ('iqbal', 100)])

    def test_campus_tab_and_campus_war(self):
        self.award(self.iqbal, 100)
        self.award(self.nami, 50)
        self.award(self.acan, 120)
        self.client.force_login(self.iqbal)
        res = self.client.get(reverse('social:leaderboard'), {'tab': 'campus'})
        self.assertEqual([u.username for u in res.context['ranking']], ['iqbal', 'nami'])
        war = {c.short_name: c.avg_xp for c in self.client.get(reverse('social:campus_war')).context['campuses']}
        self.assertEqual((war['ITB'], war['UI']), (120, 75))

    def test_weekly_report_ranks_by_weekly_xp(self):
        import json
        self.award(self.nami, 500)
        self.age(self.nami, 10)  # di luar 7 hari: tidak masuk peringkat mingguan
        self.award(self.nami, 40)
        self.award(self.iqbal, 60)
        self.award(self.acan, 90)
        Friendship.objects.create(from_user=self.iqbal, to_user=self.nami, status=Friendship.ACCEPTED)
        self.client.force_login(self.iqbal)
        rank = json.loads(self.client.get(reverse('challenge:list')).context['rank_json'])
        self.assertEqual([(r['name'], r['xp']) for r in rank['nasional']], [('acan', 90), ('iqbal', 60), ('nami', 40)])
        self.assertEqual([r['name'] for r in rank['kampus']], ['iqbal', 'nami'])
        self.assertEqual([r['name'] for r in rank['teman']], ['iqbal', 'nami'])
        self.assertTrue(rank['nasional'][1]['is_me'])


class LeaderboardSeedTests(TestCase):
    """Akun contoh leaderboard: XP total tetap, riwayat mingguan ada, akun asli tidak disentuh."""

    def run_seed(self):
        from gamification.models import GameProfile
        from social import seed
        from social.models import CampusMembership, XPActivity
        seed.ensure_canteens(University, Canteen, log=lambda *a: None)
        return seed.seed_leaderboard(User, University, CampusMembership, GameProfile, XPActivity,
                                     timezone.localtime(), log=lambda *a: None)

    def test_seed_is_idempotent_and_natural(self):
        from gamification.models import GameProfile
        from social import seed
        from social.models import XPActivity
        from social.services import users_with_xp
        User.objects.create_user('zahra.aulia', password='rahasia123')  # akun asli dengan nama sama
        entries = seed.load_leaderboard_entries()
        self.run_seed()
        self.run_seed()

        self.assertFalse(GameProfile.objects.filter(user__username='zahra.aulia').exists())
        seeded = len(entries) - 1
        self.assertEqual(GameProfile.objects.count(), seeded)
        totals = {e['username']: e['total_xp'] for e in entries}
        for p in GameProfile.objects.select_related('user'):
            self.assertEqual(p.total_xp, totals[p.user.username])  # signal tidak menambah XP
            logged = sum(XPActivity.objects.filter(user=p.user).values_list('amount', flat=True))
            self.assertLessEqual(logged, p.total_xp)

        weekly = list(users_with_xp(since=timezone.localdate() - timedelta(days=6)))
        self.assertGreater(len(weekly), 10)
        self.assertNotIn('fajar.nugroho', [u.username for u in weekly])  # akun "libur" minggu ini
        self.assertEqual(users_with_xp().first().username, 'fajar.nugroho')
        self.assertEqual(User.objects.get(username='bima.aditya').campus.university.short_name, 'UI')
