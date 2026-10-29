from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import StoryComic, StoryPage


class StoryEditorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        StoryComic.objects.all().delete()
        
        User = get_user_model()
        cls.editor = User.objects.create_user(username='editor', is_staff=True)
        cls.member = User.objects.create_user(username='member')
        cls.comic = StoryComic.objects.create(bab=1, title='Bab awal', is_published=False)
        cls.page = StoryPage.objects.create(
            comic=cls.comic, position=1, title='Awal perjalanan', narration='Narasi lengkap.',
            dialogue_one='Apa yang kita pelajari?', dialogue_two='Asal-usul makanan.',
            takeaway='Kenali isi piring.', action='Periksa satu bahan makanan.',
        )

    def setUp(self):
        self.client.force_login(self.editor)

    def page_data(self, **changes):
        data = {
            'position': 2, 'title': 'Halaman baru', 'scene': 'farm', 'narration': 'Narasi halaman baru.',
            'speaker_one': 'Alya', 'dialogue_one': 'Dari mana asal makan siang kita?',
            'speaker_two': 'Tunas', 'dialogue_two': 'Mari kita cari tahu.',
            'takeaway': 'Makanan punya perjalanan.', 'action': 'Kenali satu bahannya.',
            'source_label': '', 'source_url': '',
        }
        data.update(changes)
        return data

    def test_staff_can_create_edit_and_delete_chapter(self):
        create = self.client.post(reverse('story:comic_create'), {
            'bab': 7, 'title': 'Bab baru', 'description': 'Cerita baru.', 'unlock_level': 2,
        })
        self.assertRedirects(create, reverse('story:manage'))
        comic = StoryComic.objects.get(bab=7)
        self.assertFalse(comic.is_published)
        edit = self.client.post(reverse('story:comic_edit', args=[comic.pk]), {
            'bab': 7, 'title': 'Judul diperbarui', 'description': 'Ringkasan baru.', 'unlock_level': 3,
        })
        self.assertRedirects(edit, reverse('story:manage'))
        comic.refresh_from_db()
        self.assertEqual(comic.title, 'Judul diperbarui')
        self.assertEqual(self.client.get(reverse('story:comic_delete', args=[comic.pk])).status_code, 200)
        self.assertTrue(StoryComic.objects.filter(pk=comic.pk).exists())
        self.client.post(reverse('story:comic_delete', args=[comic.pk]))
        self.assertFalse(StoryComic.objects.filter(pk=comic.pk).exists())

    def test_staff_can_create_edit_read_and_delete_page(self):
        result = self.client.post(reverse('story:page_create', args=[self.comic.pk]), self.page_data())
        self.assertRedirects(result, reverse('story:manage'))
        page = self.comic.pages.get(position=2)
        edit = self.client.post(reverse('story:page_edit', args=[self.comic.pk, page.pk]), self.page_data(title='Judul diperbarui'))
        self.assertRedirects(edit, reverse('story:manage'))
        page.refresh_from_db()
        self.assertEqual(page.title, 'Judul diperbarui')
        preview = self.client.get(reverse('story:story_reader', args=[1]), {'page': 2})
        self.assertContains(preview, 'Judul diperbarui')
        self.assertEqual(self.client.get(reverse('story:page_delete', args=[self.comic.pk, page.pk])).status_code, 200)
        self.assertTrue(StoryPage.objects.filter(pk=page.pk).exists())
        self.client.post(reverse('story:page_delete', args=[self.comic.pk, page.pk]))
        self.assertFalse(StoryPage.objects.filter(pk=page.pk).exists())
        self.comic.refresh_from_db()
        self.assertEqual(self.comic.total_pages, 1)

    def test_member_cannot_access_editor_or_modify_content(self):
        self.client.force_login(self.member)
        routes = [
            reverse('story:manage'), reverse('story:comic_create'),
            reverse('story:comic_edit', args=[self.comic.pk]),
            reverse('story:comic_delete', args=[self.comic.pk]),
            reverse('story:page_create', args=[self.comic.pk]),
            reverse('story:page_edit', args=[self.comic.pk, self.page.pk]),
            reverse('story:page_delete', args=[self.comic.pk, self.page.pk]),
        ]
        for url in routes:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)
                self.assertEqual(self.client.post(url, {}).status_code, 403)
        self.assertTrue(StoryComic.objects.filter(pk=self.comic.pk).exists())
        self.assertTrue(StoryPage.objects.filter(pk=self.page.pk).exists())

    def test_duplicate_page_position_is_a_form_error(self):
        response = self.client.post(reverse('story:page_create', args=[self.comic.pk]), self.page_data(position=1))
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'position', 'Urutan ini sudah dipakai halaman lain di bab yang sama.')
        self.assertEqual(self.comic.pages.count(), 1)

    def test_page_cannot_be_edited_through_another_chapter(self):
        other = StoryComic.objects.create(bab=8, title='Bab lain', is_published=False)
        response = self.client.post(reverse('story:page_edit', args=[other.pk, self.page.pk]), self.page_data())
        self.assertEqual(response.status_code, 404)

    def test_chapter_without_pages_cannot_be_published(self):
        response = self.client.post(reverse('story:comic_create'), {
            'bab': 9, 'title': 'Bab kosong', 'description': 'Ringkasan.', 'unlock_level': 1, 'is_published': 'on',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('is_published', response.context['form'].errors)
        self.assertFalse(StoryComic.objects.filter(bab=9).exists())

    def test_deleting_last_page_unpublishes_chapter(self):
        self.comic.is_published = True
        self.comic.save()
        self.client.post(reverse('story:page_delete', args=[self.comic.pk, self.page.pk]))
        self.comic.refresh_from_db()
        self.assertEqual(self.comic.total_pages, 0)
        self.assertFalse(self.comic.is_published)

    def test_editor_forms_require_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.editor)
        response = client.post(reverse('story:page_create', args=[self.comic.pk]), self.page_data())
        self.assertEqual(response.status_code, 403)

    def test_editor_content_is_escaped_in_reader(self):
        self.page.dialogue_one = '<script>alert("unsafe")</script>'
        self.page.save()
        response = self.client.get(reverse('story:story_reader', args=[1]))
        self.assertContains(response, '&lt;script&gt;')
        self.assertNotContains(response, '<script>alert("unsafe")</script>')
