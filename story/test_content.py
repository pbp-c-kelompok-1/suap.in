from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from .models import StoryComic, StoryPage


class StoryContentTests(TestCase):
    def seed(self):
        call_command('seed_stories', stdout=StringIO())

    def test_six_complete_chapters_have_twenty_five_pages(self):
        self.seed()
        self.assertEqual(StoryComic.objects.count(), 6)
        self.assertEqual(StoryPage.objects.count(), 25)
        self.assertEqual(list(StoryComic.objects.values_list('total_pages', flat=True)), [4, 3, 4, 5, 3, 6])
        for comic in StoryComic.objects.all():
            self.assertEqual(list(comic.pages.values_list('position', flat=True)), list(range(1, comic.total_pages + 1)))
        for page in StoryPage.objects.all():
            self.assertTrue(page.narration and page.dialogue_one and page.dialogue_two)
            self.assertTrue(page.takeaway and page.action and page.source_url.startswith('https://'))
            self.assertNotIn('segera hadir', page.narration.lower())

    def test_repeat_seed_preserves_content_edits_and_does_not_duplicate(self):
        self.seed()
        page = StoryPage.objects.first()
        page.dialogue_one = 'Editan asli dari editor.'
        page.save()
        self.seed()
        page.refresh_from_db()
        self.assertEqual(page.dialogue_one, 'Editan asli dari editor.')
        self.assertEqual(StoryPage.objects.count(), 25)
        self.assertEqual(StoryComic.objects.count(), 6)
