import io
from unittest.mock import patch
from PIL import Image

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from scanner.models import CarbonBudget, FoodItem, FoodLog
from scanner.services import (
    box_to_percent,
    calculate_carbon_analogy,
    find_food_item,
    get_carbon_status,
    match_food_items_to_db,
)
from scanner.views import (
    DEFAULT_BUDGET_GRAMS,
    collect_items,
    get_today_budget,
    meal_slot_for,
    to_float,
)


class ScannerViewAndServiceTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='scannertester',
            password='Password123!',
        )
        self.food_item = FoodItem.objects.create(
            name='Nasi Goreng',
            category='rice',
            co2_per_serving_grams=420.0,
        )

    def _generate_dummy_image(self):
        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), color='green')
        image.save(file, 'jpeg')
        file.seek(0)
        return SimpleUploadedFile('test.jpg', file.read(), content_type='image/jpeg')

    def test_services_helpers(self):
        self.assertIsNone(to_float('invalid'))
        self.assertEqual(to_float('12,5'), 12.5)
        self.assertEqual(meal_slot_for(7), 'sarapan')
        self.assertEqual(meal_slot_for(12), 'siang')
        self.assertEqual(meal_slot_for(16), 'camilan')
        self.assertEqual(meal_slot_for(20), 'malam')

        # Carbon status & analogy
        color, label = get_carbon_status(300, 2000)
        self.assertEqual(color, 'green')

        analogy = calculate_carbon_analogy(1000)
        self.assertIn('motor', analogy)

        # box_to_percent
        box = {'y_min': 100, 'x_min': 200, 'y_max': 800, 'x_max': 900}
        pct = box_to_percent(box)
        self.assertEqual(pct['top'], '10.00')

        # find_food_item
        found = find_food_item('Nasi Goreng')
        self.assertIsNotNone(found)

        # match_food_items_to_db
        matched = match_food_items_to_db([{'name': 'Nasi Goreng', 'co2_grams': 500}])
        self.assertEqual(len(matched), 1)

    def test_scan_view_get(self):
        response = self.client.get(reverse('scanner:scan'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'scanner/scan.html')

    @patch('scanner.views.detect_food_from_image')
    def test_scan_view_post_valid(self, mock_detect):
        self.client.force_login(self.user)
        mock_detect.return_value = (
            {
                'detected_items': [{'name': 'Nasi Goreng', 'co2_grams': 450, 'box': None}],
                'notes': 'Test scan',
            },
            '{"mock": "response"}',
        )
        img = self._generate_dummy_image()
        response = self.client.post(reverse('scanner:scan'), {'photo': img})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('scanner:result'))

    def test_result_view_redirects_without_session(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('scanner:result'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('scanner:scan'))

    def test_result_view_with_session(self):
        self.client.force_login(self.user)
        session = self.client.session
        session['scan_result'] = {
            'detected_items': [{'name': 'Nasi Goreng', 'co2_grams': 450}],
            'notes': 'Test note',
        }
        session['scan_photo'] = 'data:image/jpeg;base64,abc'
        session.save()

        response = self.client.get(reverse('scanner:result'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'scanner/result.html')

    def test_save_log_view(self):
        self.client.force_login(self.user)
        session = self.client.session
        session['scan_result'] = {
            'detected_items': [{'name': 'Nasi Goreng', 'co2_grams': 450}],
            'notes': 'Saved meal note',
        }
        session['scan_raw'] = '{"mock": "raw"}'
        session.save()

        response = self.client.post(reverse('scanner:save_log'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('scanner:daily_log'))

        self.assertTrue(FoodLog.objects.filter(user=self.user, custom_name='Nasi Goreng').exists())
        budget = CarbonBudget.objects.get(user=self.user, date=timezone.localdate())
        self.assertEqual(budget.used_grams, 450)

    def test_daily_log_view_and_delete(self):
        self.client.force_login(self.user)
        log = FoodLog.objects.create(
            user=self.user,
            food_item=self.food_item,
            custom_name='Nasi Goreng',
            co2_grams=450,
            scanned_at=timezone.now(),
        )
        budget = get_today_budget(self.user)
        budget.used_grams = 450
        budget.save()

        response = self.client.get(reverse('scanner:daily_log'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'scanner/daily_log.html')

        # Test delete
        del_resp = self.client.post(reverse('scanner:delete_log', args=[log.id]))
        self.assertEqual(del_resp.status_code, 302)
        self.assertFalse(FoodLog.objects.filter(id=log.id).exists())
        budget.refresh_from_db()
        self.assertEqual(budget.used_grams, 0)

    def test_api_scan_status(self):
        response = self.client.get(reverse('scanner:api_status'))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'has_result': False})

        session = self.client.session
        session['scan_result'] = {'detected_items': []}
        session.save()
        response = self.client.get(reverse('scanner:api_status'))
        self.assertJSONEqual(response.content, {'has_result': True})
