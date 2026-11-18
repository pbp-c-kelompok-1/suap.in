"""Functional test (Selenium): menguji modul social dari browser sungguhan.

Yang dicek: aksi CRUD jalan lewat AJAX tanpa reload halaman.
Cara cek "tanpa reload": sebelum aksi, kita taruh penanda di `window`.
Kalau halaman sampai reload, penanda itu hilang.

Butuh Google Chrome + paket `selenium`. Kalau tidak ada, test ini otomatis di-skip.
Jalankan: python manage.py test social.test_functional
Opsional (kalau Chrome/driver tidak di lokasi standar): set env CHROME_BIN dan CHROMEDRIVER.
"""
# =====================================================================================
# FUNCTIONAL TEST (Selenium) = test dari sudut pandang pengguna: membuka Chrome sungguhan
# (headless = tanpa jendela), mengetik, dan mengklik tombol seperti manusia.
# StaticLiveServerTestCase menjalankan server Django sementara (self.live_server_url)
# lengkap dengan file static (CSS/JS), supaya JavaScript AJAX ikut jalan.
# =====================================================================================
import os
import unittest

from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.cache import cache
from django.test import tag
from django.urls import reverse

from .models import CampusMembership, Friendship, University

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import Select, WebDriverWait
except ImportError:  # selenium belum di-install
    webdriver = None

# Waktu tunggu maksimal (detik) menunggu elemen muncul setelah AJAX.
WAIT_SECONDS = 10


# Buat Chrome headless. --no-sandbox & --disable-dev-shm-usage diperlukan di server/CI (Linux).
# CHROME_BIN / CHROMEDRIVER opsional kalau Chrome tidak di lokasi standar.
def make_browser():
    options = webdriver.ChromeOptions()
    for arg in ('--headless=new', '--no-sandbox', '--disable-dev-shm-usage', '--window-size=1280,900'):
        options.add_argument(arg)
    if os.environ.get('CHROME_BIN'):
        options.binary_location = os.environ['CHROME_BIN']
    service = Service(os.environ['CHROMEDRIVER']) if os.environ.get('CHROMEDRIVER') else Service()
    return webdriver.Chrome(options=options, service=service)


# @tag('functional') -> bisa dijalankan/dilewati terpisah: python manage.py test --tag=functional
@tag('functional')
class SocialFunctionalTests(StaticLiveServerTestCase):

    # Sekali di awal: buka Chrome. Kalau selenium/Chrome tidak ada -> SkipTest (test dilewati,
    # bukan gagal), supaya CI tetap hijau di mesin tanpa Chrome.
    @classmethod
    def setUpClass(cls):
        if webdriver is None:
            raise unittest.SkipTest('selenium belum di-install (pip install selenium)')
        try:
            cls.browser = make_browser()
        except Exception as exc:  # Chrome/driver tidak tersedia di mesin ini
            raise unittest.SkipTest(f'Chrome tidak bisa dijalankan: {exc}')
        super().setUpClass()

    # Sekali di akhir: tutup Chrome.
    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'browser') and cls.browser is not None:
            try:
                cls.browser.quit()
            except Exception:
                pass
        super().tearDownClass()

    # Sebelum setiap test: kosongkan rate limit, buat 2 user & 2 kampus.
    def setUp(self):
        cache.clear()
        self.iqbal = User.objects.create_user('iqbal', password='pass12345x')
        self.nami = User.objects.create_user('nami', password='pass12345x')
        self.ui = University.objects.create(name='Universitas Indonesia', short_name='UI', city='Depok')
        self.itb = University.objects.create(name='Institut Teknologi Bandung', short_name='ITB', city='Bandung')

    # ---------- helper ----------

    # Login TANPA mengisi form: force_login membuat session, lalu cookie sessionid ditempel ke Chrome.
    # Chrome harus membuka halaman di domain yang sama dulu sebelum boleh menambah cookie.
    def login_as(self, user):
        """Login tanpa mengisi form: pakai session dari test client, lalu tempel cookie-nya."""
        self.client.force_login(user)
        self.browser.get(self.live_server_url + '/static/__login__')  # harus di domain yang sama dulu
        self.browser.delete_all_cookies()
        self.browser.add_cookie({'name': 'sessionid', 'value': self.client.cookies['sessionid'].value, 'path': '/'})

    # Buka halaman lalu pasang PENANDA window.__noReload = true.
    # Variabel window hilang kalau halaman reload -> dipakai assert_no_reload.
    def open(self, url_name, query=''):
        self.browser.get(self.live_server_url + reverse(url_name) + query)
        self.browser.execute_script('window.__noReload = true;')

    # Kalau penanda masih ada -> halaman tidak reload -> update terbukti lewat AJAX.
    def assert_no_reload(self):
        self.assertTrue(self.browser.execute_script('return window.__noReload === true;'),
                        'Halaman ter-reload, padahal seharusnya lewat AJAX')

    # WebDriverWait = tunggu sampai kondisi terpenuhi (maks WAIT_SECONDS).
    def wait(self):
        return WebDriverWait(self.browser, WAIT_SECONDS)

    # Tunggu sampai elemen CSS tertentu berisi teks tertentu.
    def wait_text(self, css, text):
        self.wait().until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, css), text))

    # ---------- skenario ----------

    # Skenario 1: iqbal cari "nam" -> klik Tambah -> pesan muncul tanpa reload -> baris PENDING.
    # Lalu nami login -> klik Terima -> berteman, juga tanpa reload.
    def test_send_and_accept_friend_request_without_reload(self):
        self.login_as(self.iqbal)
        self.open('social:friends')
        self.browser.find_element(By.ID, 'friendQuery').send_keys('nam')
        add = self.wait().until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '#friendsRegion form[action$="/friends/request/"] button')))
        add.click()
        self.wait_text('#friendMsg', 'Permintaan pertemanan dikirim ke nami.')
        self.wait_text('#friendsRegion', 'Permintaan terkirim')
        self.assert_no_reload()
        self.assertEqual(Friendship.objects.get().status, Friendship.PENDING)

        self.login_as(self.nami)
        self.open('social:friends')
        self.browser.find_element(By.CSS_SELECTOR, 'input[name="action"][value="accept"] + button').click()
        self.wait_text('#friendMsg', 'Kamu sekarang berteman dengan iqbal!')
        self.wait_text('#friendsRegion', '1 teman')
        self.assert_no_reload()
        self.assertEqual(Friendship.objects.get().status, Friendship.ACCEPTED)

    # Skenario 2: tombol "basi": Tambah sudah tampil, lalu (di server) mereka ternyata sudah berteman.
    # Klik -> server membalas 400 "Kamu sudah berteman" -> pesan merah tampil tanpa reload.
    def test_stale_button_shows_error_from_server(self):
        """Tombol "Tambah" sudah tampil, tapi sebelum diklik ternyata sudah berteman (mis. dari tab lain)."""
        self.login_as(self.iqbal)
        self.open('social:friends', '?q=nami')
        add = self.browser.find_element(By.CSS_SELECTOR, '#friendsRegion form[action$="/friends/request/"] button')
        Friendship.objects.create(from_user=self.nami, to_user=self.iqbal, status=Friendship.ACCEPTED)
        add.click()
        self.wait_text('#friendMsg', 'Kamu sudah berteman dengan nami.')
        self.wait_text('#friendsRegion', 'Sudah berteman')
        self.assertIn('err', self.browser.find_element(By.ID, 'friendMsg').get_attribute('class'))
        self.assert_no_reload()
        self.assertEqual(Friendship.objects.count(), 1)

    # Skenario 3: klik tab leaderboard -> isi peringkat berganti tanpa reload (?partial=1).
    def test_leaderboard_tabs_switch_without_reload(self):
        from .tests import scan
        scan(self.iqbal, 450, times=3)
        self.login_as(self.iqbal)
        self.open('social:leaderboard')
        self.wait_text('#rankRegion', 'iqbal')

        self.browser.find_element(By.CSS_SELECTOR, '#rankTabs [data-tab="campus"]').click()
        self.wait_text('#rankRegion', 'Kamu belum memilih kampus')
        self.assertIn('tab=campus', self.browser.current_url)
        selected = self.browser.find_element(By.CSS_SELECTOR, '#rankTabs [aria-selected="true"]')
        self.assertEqual(selected.get_attribute('data-tab'), 'campus')
        self.assert_no_reload()

    # Skenario 4: pilih kampus di Campus War -> tersimpan dan tampilan berubah tanpa reload.
    def test_choose_campus_without_reload(self):
        self.login_as(self.iqbal)
        self.open('social:campus_war')
        self.assertEqual(self.browser.find_element(By.ID, 'myCampus').text, 'belum dipilih')

        Select(self.browser.find_element(By.CSS_SELECTOR, '#campusForm select')).select_by_visible_text('ITB')
        self.browser.find_element(By.CSS_SELECTOR, '#campusForm button').click()
        self.wait_text('#campusMsg', 'Kampusmu sekarang ITB.')
        self.wait_text('#campusRegion', '1 mahasiswa')
        self.assertEqual(self.browser.find_element(By.ID, 'myCampus').text, 'ITB')
        self.assert_no_reload()
        self.assertEqual(CampusMembership.objects.get(user=self.iqbal).university, self.itb)
