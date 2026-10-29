from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from gamification.models import GameProfile
from .models import StoryComic, StoryPage


class CompleteStoryReaderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_stories', stdout=StringIO())
        cls.user = get_user_model().objects.create_user(username='reader')
        GameProfile.objects.create(user=cls.user, level=50, total_xp=14700)

    def setUp(self):
        self.client.force_login(self.user)

    def test_every_seeded_page_displays_its_real_content(self):
        for page in StoryPage.objects.select_related('comic'):
            with self.subTest(chapter=page.comic.bab, page=page.position):
                response = self.client.get(reverse('story:story_reader', args=[page.comic.bab]), {'page': page.position})
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, page.title)
                self.assertContains(response, page.dialogue_one)
                self.assertContains(response, page.dialogue_two)
                self.assertContains(response, page.takeaway)
                self.assertNotContains(response, 'Panel komik segera hadir')

    def test_invalid_page_numbers_cannot_crash_reader(self):
        for value, expected in [('huruf', 1), ('0', 1), ('-7', 1), ('999999999', 4)]:
            with self.subTest(value=value):
                response = self.client.get(reverse('story:story_reader', args=[1]), {'page': value})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context['current_page'], expected)

    def test_navigation_uses_actual_pages_even_if_cached_total_is_wrong(self):
        StoryComic.objects.filter(bab=1).update(total_pages=999)
        response = self.client.get(reverse('story:story_reader', args=[1]), {'page': 4})
        self.assertEqual(response.context['page_count'], 4)
        self.assertFalse(response.context['has_next'])
        self.assertTrue(response.context['has_prev'])

    def test_unpublished_chapters_are_hidden_from_reader_and_ajax(self):
        StoryComic.objects.filter(bab=2).update(is_published=False)
        self.assertEqual(self.client.get(reverse('story:story_reader', args=[2])).status_code, 404)
        response = self.client.get(reverse('story:story_list'), HTTP_ACCEPT='application/json')
        self.assertEqual(response.json()['count'], 5)
        self.assertNotIn('Jejak yang Tak Terlihat', response.json()['html'])

    def test_database_filters_return_correct_ajax_results(self):
        GameProfile.objects.filter(user=self.user).update(level=1, total_xp=0)
        for status, count in [('unlocked', 1), ('locked', 5), ('all', 6)]:
            with self.subTest(status=status):
                response = self.client.get(reverse('story:story_list'), {'status': status}, HTTP_ACCEPT='application/json')
                self.assertEqual(response.json()['count'], count)
        result = self.client.get(reverse('story:story_list'), {'q': 'Ladang'}, HTTP_ACCEPT='application/json').json()
        self.assertEqual(result['count'], 1)
        self.assertIn('Dari Ladang ke Piring', result['html'])

    def test_guest_cannot_fetch_story_data(self):
        self.client.logout()
        response = self.client.get(reverse('story:story_list'), HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/auth/login/'))


class EmptyStoryDatabaseTests(TestCase):
    def test_empty_story(self):
        # Sengaja dikosongin buat ngecek halaman tanpa cerita.
        StoryComic.objects.all().delete()

        user = get_user_model().objects.create_user(
            username='empty_reader',
        )
        self.client.force_login(user)

        response = self.client.get(
            reverse('story:story_list'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(StoryComic.objects.count(), 0)
        self.assertEqual(StoryPage.objects.count(), 0)
