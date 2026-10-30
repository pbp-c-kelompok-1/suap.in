from datetime import timedelta
import time
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from authentication.forms import (
    ForgotPasswordForm,
    LoginForm,
    NewPasswordForm,
    OtpForm,
    RegisterForm,
)
from authentication.views import OTP_SESSION_KEY, build_weekly_chart
from scanner.models import FoodLog


class AuthenticationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = 'P@ssword123!'
        self.user = User.objects.create_user(
            username='syahidtest',
            email='syahid@example.com',
            password=self.password,
            first_name='Syahid',
        )

    def test_register_view_get(self):
        response = self.client.get(reverse('authentication:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'authentication/register.html')

    def test_register_view_already_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('authentication:register'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('gamification:dashboard'))

    def test_register_view_post_valid(self):
        data = {
            'username': 'newuser123',
            'email': 'newuser@example.com',
            'password1': 'SecurePassword123!',
            'password2': 'SecurePassword123!',
        }
        response = self.client.post(reverse('authentication:register'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser123').exists())

    def test_register_view_post_invalid(self):
        data = {
            'username': 'syahidtest',
            'email': 'invalid-email',
            'password': '123',
            'confirm_password': '456',
        }
        response = self.client.post(reverse('authentication:register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)

    def test_login_view_get(self):
        response = self.client.get(reverse('authentication:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'authentication/login.html')

    def test_login_view_already_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('authentication:login'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('gamification:dashboard'))

    def test_login_view_post_username_success(self):
        data = {
            'identifier': 'syahidtest',
            'password': self.password,
            'remember': 'on',
        }
        response = self.client.post(reverse('authentication:login'), data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('gamification:dashboard'))

    def test_login_view_post_email_success(self):
        data = {
            'identifier': 'syahid@example.com',
            'password': self.password,
            'remember': False,
        }
        response = self.client.post(reverse('authentication:login'), data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('gamification:dashboard'))

    def test_login_view_post_wrong_password(self):
        data = {
            'identifier': 'syahidtest',
            'password': 'WrongPassword123',
            'remember': False,
        }
        response = self.client.post(reverse('authentication:login'), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email/username atau password salah.')

    def test_logout_view(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('authentication:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('authentication:login'))

    def test_forgot_password_flow(self):
        # Step 1: Request OTP
        response = self.client.get(reverse('authentication:forgot_password'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse('authentication:forgot_password'),
            {'email': 'syahid@example.com'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('authentication:verify_otp'))

        session = self.client.session
        self.assertIn(OTP_SESSION_KEY, session)
        code = session[OTP_SESSION_KEY]['code']

        # Step 2: Verify OTP
        response = self.client.get(reverse('authentication:verify_otp'))
        self.assertEqual(response.status_code, 200)

        # Wrong code
        response = self.client.post(reverse('authentication:verify_otp'), {'code': '000000'})
        self.assertEqual(response.status_code, 200)

        # Correct code
        response = self.client.post(reverse('authentication:verify_otp'), {'code': code})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('authentication:reset_password'))

        # Step 3: Reset Password
        response = self.client.get(reverse('authentication:reset_password'))
        self.assertEqual(response.status_code, 200)

        new_pass = 'BrandNewP@ssword999!'
        response = self.client.post(
            reverse('authentication:reset_password'),
            {'password1': new_pass, 'password2': new_pass},
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('authentication:password_changed'))

        # Step 4: Password changed page
        response = self.client.get(reverse('authentication:password_changed'))
        self.assertEqual(response.status_code, 200)

    def test_verify_otp_without_session(self):
        response = self.client.get(reverse('authentication:verify_otp'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('authentication:forgot_password'))

    def test_reset_password_without_verified_session(self):
        response = self.client.get(reverse('authentication:reset_password'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('authentication:forgot_password'))

    def test_profile_view_and_chart(self):
        FoodLog.objects.create(
            user=self.user,
            custom_name='Nasi Goreng',
            co2_grams=450.0,
            scanned_at=timezone.now(),
        )
        FoodLog.objects.create(
            user=self.user,
            custom_name='Tahu Tempe',
            co2_grams=120.0,
            scanned_at=timezone.now() - timedelta(days=2),
        )

        response = self.client.get(reverse('authentication:profile', args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['scan_count'], 2)
        self.assertEqual(response.context['total_co2'], 570)
        self.assertTrue(response.context['chart']['has_data'])

        # Chart helper test
        chart = build_weekly_chart(self.user)
        self.assertEqual(len(chart['points']), 7)
