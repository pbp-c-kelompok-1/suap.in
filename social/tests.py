import io
import shutil
import tempfile
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from .models import Canteen, CommunityPost, University


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
