import secrets
import time
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from scanner.models import FoodLog

from .forms import (
    ForgotPasswordForm,
    LoginForm,
    NewPasswordForm,
    OtpForm,
    RegisterForm,
)

OTP_SESSION_KEY = 'password_reset'
OTP_LIFETIME_SECONDS = 600
OTP_MAX_ATTEMPTS = 5


def register_view(request):
    if request.user.is_authenticated:
        return redirect('gamification:dashboard')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f'Selamat datang, {user.username}!')
        return redirect('gamification:dashboard')

    return render(request, 'authentication/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('gamification:dashboard')

    next_url = request.POST.get('next') or request.GET.get('next') or ''
    if not url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = ''

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        identifier = form.cleaned_data['identifier'].strip()
        username = identifier
        if '@' in identifier:
            match = User.objects.filter(email__iexact=identifier).first()
            if match:
                username = match.get_username()

        user = authenticate(request, username=username, password=form.cleaned_data['password'])
        if user is not None:
            login(request, user)
            if not form.cleaned_data['remember']:
                request.session.set_expiry(0)
            return redirect(next_url or 'gamification:dashboard')
        form.add_error(None, 'Email/username atau password salah.')

    return render(request, 'authentication/login.html', {'form': form, 'next': next_url})


def logout_view(request):
    logout(request)
    messages.success(request, 'Kamu sudah keluar.')
    return redirect('authentication:login')


def forgot_password_view(request):
    form = ForgotPasswordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email'].strip().lower()
        user = User.objects.filter(email__iexact=email).first()
        code = f'{secrets.randbelow(10 ** 6):06d}'

        if user:
            send_mail(
                subject='Kode verifikasi Suap.in',
                message=(
                    f'Halo {user.username},\n\n'
                    f'Kode verifikasi untuk reset password kamu adalah: {code}\n'
                    f'Kode berlaku selama {OTP_LIFETIME_SECONDS // 60} menit.\n\n'
                    'Abaikan email ini jika kamu tidak merasa memintanya.'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )

        request.session[OTP_SESSION_KEY] = {
            'user_id': user.pk if user else None,
            'email': email,
            'code': code,
            'expires': time.time() + OTP_LIFETIME_SECONDS,
            'attempts': 0,
            'verified': False,
        }
        return redirect('authentication:verify_otp')

    return render(request, 'authentication/forgot_password.html', {'form': form})


def verify_otp_view(request):
    state = request.session.get(OTP_SESSION_KEY)
    if not state:
        return redirect('authentication:forgot_password')

    form = OtpForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        if time.time() > state['expires'] or state['attempts'] >= OTP_MAX_ATTEMPTS:
            request.session.pop(OTP_SESSION_KEY, None)
            messages.error(request, 'Kode sudah kedaluwarsa. Minta kode baru.')
            return redirect('authentication:forgot_password')

        if state['user_id'] and secrets.compare_digest(form.cleaned_data['code'], state['code']):
            state['verified'] = True
            request.session[OTP_SESSION_KEY] = state
            return redirect('authentication:reset_password')

        state['attempts'] += 1
        request.session[OTP_SESSION_KEY] = state
        form.add_error('code', 'Kode tidak valid.')

    context = {'form': form, 'email': state['email']}
    return render(request, 'authentication/verify_otp.html', context)


def reset_password_view(request):
    state = request.session.get(OTP_SESSION_KEY)
    if not state or not state.get('verified') or not state.get('user_id'):
        return redirect('authentication:forgot_password')

    user = get_object_or_404(User, pk=state['user_id'])
    form = NewPasswordForm(user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user.set_password(form.cleaned_data['password1'])
        user.save()
        request.session.pop(OTP_SESSION_KEY, None)
        return redirect('authentication:password_changed')

    return render(request, 'authentication/reset_password.html', {'form': form})


def password_changed_view(request):
    return render(request, 'authentication/password_changed.html')


def build_weekly_chart(user):
    today = timezone.localdate()
    start = today - timedelta(days=6)
    rows = (
        FoodLog.objects.filter(user=user, scanned_at__date__gte=start)
        .annotate(day=TruncDate('scanned_at'))
        .values('day')
        .annotate(total=Sum('co2_grams'))
    )
    totals = {row['day']: row['total'] or 0 for row in rows}

    day_names = ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min']
    width, height, pad_top, pad_bottom = 560, 170, 18, 18
    column = width / 7
    days = [start + timedelta(days=i) for i in range(7)]
    values = [totals.get(day, 0) for day in days]
    peak = max(values) or 1

    points = []
    for index, (day, value) in enumerate(zip(days, values)):
        x = column * (index + 0.5)
        y = pad_top + (height - pad_top - pad_bottom) * (1 - value / peak)
        points.append({
            'x': f'{x:.1f}',
            'y': f'{y:.1f}',
            'label': day_names[day.weekday()],
            'value': round(value),
        })

    return {
        'width': width,
        'height': height,
        'polyline': ' '.join(f"{p['x']},{p['y']}" for p in points),
        'points': points,
        'has_data': any(values),
    }


def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    logs = FoodLog.objects.filter(user=profile_user)
    stats = logs.aggregate(scans=Count('id'), total_co2=Sum('co2_grams'))
    active_days = (
        logs.annotate(day=TruncDate('scanned_at')).order_by().values('day').distinct().count()
    )

    context = {
        'profile_user': profile_user,
        'is_own_profile': request.user.is_authenticated and request.user == profile_user,
        'scan_count': stats['scans'] or 0,
        'total_co2': round(stats['total_co2'] or 0),
        'active_days': active_days,
        'chart': build_weekly_chart(profile_user),
    }
    return render(request, 'authentication/profile.html', context)
