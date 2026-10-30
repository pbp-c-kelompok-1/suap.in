from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from gamification.models import GameProfile
from gamification.services import award_xp

from .models import StoryComic, StoryPage


class StoryProgressionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        StoryComic.objects.all().delete()
        
        User = get_user_model()
        cls.beginner = User.objects.create_user(username="beginner")
        cls.experienced = User.objects.create_user(username="experienced")
        GameProfile.objects.create(user=cls.experienced, total_xp=300, level=5)
        cls.first_comic = StoryComic.objects.create(
            bab=1, title="Dari Ladang ke Piring", unlock_level=1, total_pages=4,
        )
        cls.locked_comic = StoryComic.objects.create(
            bab=2, title="Jejak yang Tak Terlihat", unlock_level=5, total_pages=3,
        )

        for comic in [cls.first_comic, cls.locked_comic]:
            StoryPage.objects.create(
                comic=comic, position=1, title='Halaman uji', narration='Narasi uji.',
                dialogue_one='Pertanyaan uji.', dialogue_two='Jawaban uji.',
                takeaway='Pelajaran uji.', action='Aksi uji.',
            )

    def test_guest_must_log_in_to_view_story_list(self):
        response = self.client.get(reverse("story:story_list"))
        self.assertRedirects(response, "/auth/login/?next=/story/")

    def test_guest_must_log_in_to_read_a_comic(self):
        response = self.client.get(reverse("story:story_reader", args=[1]))
        self.assertRedirects(response, "/auth/login/?next=/story/1/")

    def test_new_account_starts_at_level_one(self):
        self.client.force_login(self.beginner)
        response = self.client.get(reverse("story:story_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(GameProfile.objects.filter(user=self.beginner).exists())
        self.assertEqual(response.context["user_level"], 1)
        self.assertEqual(response.context["user_title"], "Pemula Sadar")
        self.assertEqual(response.context["xp_current"], 0)
        self.assertEqual(response.context["xp_remaining"], 60)
        self.assertEqual(response.context["xp_percentage"], 0)
        self.assertEqual(response.context["next_level"], 2)
        self.assertEqual(
            [item["is_unlocked"] for item in response.context["comics"]],
            [True, False],
        )

    def test_progress_belongs_to_the_logged_in_account(self):
        self.client.force_login(self.experienced)
        experienced_response = self.client.get(reverse("story:story_list"))
        self.assertEqual(experienced_response.context["user_level"], 5)
        self.assertTrue(experienced_response.context["comics"][1]["is_unlocked"])

        self.client.force_login(self.beginner)
        beginner_response = self.client.get(reverse("story:story_list"))
        self.assertEqual(beginner_response.context["user_level"], 1)
        self.assertFalse(beginner_response.context["comics"][1]["is_unlocked"])

    def test_progress_is_displayed_as_xp_instead_of_scan_count(self):
        GameProfile.objects.create(user=self.beginner, total_xp=25, level=1)
        self.client.force_login(self.beginner)
        response = self.client.get(reverse("story:story_list"))

        self.assertContains(response, "25 / 60 XP")
        self.assertContains(response, "35 XP lagi ke Level 2")
        self.assertEqual(response.context["xp_percentage"], 42)
        self.assertNotContains(response, "scan lagi")

    def test_comic_unlocks_after_xp_award_reaches_required_level(self):
        GameProfile.objects.create(user=self.beginner, total_xp=299, level=4)
        self.client.force_login(self.beginner)
        before = self.client.get(reverse("story:story_list"))
        self.assertFalse(before.context["comics"][1]["is_unlocked"])

        # Posisi awal kurang 1 XP dari Level 5. Setelah ditambah, babnya harus kebuka.
        award_xp(self.beginner, 1)
        after = self.client.get(reverse("story:story_list"))
        self.assertEqual(after.context["user_level"], 5)
        self.assertTrue(after.context["comics"][1]["is_unlocked"])

    def test_direct_url_cannot_bypass_a_locked_comic(self):
        self.client.force_login(self.beginner)
        response = self.client.get(reverse("story:story_reader", args=[2]))
        self.assertRedirects(response, reverse("story:story_list"))

    def test_unlocked_comic_can_be_read(self):
        self.client.force_login(self.experienced)
        response = self.client.get(reverse("story:story_reader", args=[2]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["comic"], self.locked_comic)

    def test_max_level_does_not_offer_level_fifty_one(self):
        GameProfile.objects.create(user=self.beginner, total_xp=14700, level=50)
        self.client.force_login(self.beginner)
        response = self.client.get(reverse("story:story_list"))

        self.assertEqual(response.context["user_title"], "Legenda Lestari")
        self.assertEqual(response.context["xp_percentage"], 100)
        self.assertIsNone(response.context["next_level"])
        self.assertContains(response, "Level maksimum tercapai")
        self.assertNotContains(response, "Level 51")