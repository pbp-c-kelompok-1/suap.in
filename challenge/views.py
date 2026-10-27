import json
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST

from scanner.models import FoodLog, CarbonBudget

from .models import ChallengeProfile
from .services import (
    build_challenge_data,
    todays_quests,
    week_totals_by_day,
)

FREEZE_SESSION_KEY = 'challenge_freeze_claimed_on'


def _claimed_today(request):
    return request.session.get(FREEZE_SESSION_KEY) == timezone.localdate().isoformat()


@login_required
def challenge_list_view(request):
    today = timezone.localdate()
    week_start = today - timedelta(days=6)
    prev_week_start = week_start - timedelta(days=7)
    prev_week_end = week_start - timedelta(days=1)

    totals_by_date = week_totals_by_day(request.user, week_start, today)
    prev_totals_by_date = week_totals_by_day(request.user, prev_week_start, prev_week_end)

    this_week_kg = round(sum(totals_by_date.values()) / 1000, 2)
    prev_week_kg = round(sum(prev_totals_by_date.values()) / 1000, 2)
    has_this_week_data = bool(totals_by_date)
    has_prev_week_data = bool(prev_totals_by_date)

    delta_percent = None
    if has_this_week_data and has_prev_week_data and prev_week_kg > 0:
        delta_percent = round((this_week_kg - prev_week_kg) / prev_week_kg * 100)

    projection_kg = savings_kg = savings_trees = is_saving = None
    if has_this_week_data:
        projection_kg = round(this_week_kg / 7 * 365)
        if has_prev_week_data:
            diff_kg = prev_week_kg - this_week_kg
            is_saving = diff_kg > 0
            savings_kg = round(abs(diff_kg) * 52)
            savings_trees = round(savings_kg / 21)

    context = {
        'week_start': week_start,
        'week_end': today,
        'this_week_kg': this_week_kg,
        'prev_week_kg': prev_week_kg,
        'has_prev_week_data': has_prev_week_data,
        'delta_percent': delta_percent,
        'projection_kg': projection_kg,
        'savings_kg': savings_kg,
        'savings_trees': savings_trees,
        'is_saving': is_saving,
        'challenge_data': build_challenge_data(request.user, claimed_today=_claimed_today(request)),
    }
    return render(request, 'challenge/dashboard.html', context)




@login_required
@require_POST
def claim_freeze_view(request):
    """Klaim streak freeze setelah semua misi selesai."""
    today = timezone.localdate()

    quests, _, _, _ = todays_quests(request.user, today)

    # Jangan izinkan klaim jika misi belum tersedia atau belum selesai.
    if not quests or not all(q['val'] >= q['goal'] for q in quests):
        return JsonResponse({
            'ok': False,
            'message': 'Selesaikan semua misi terlebih dahulu.',
        }, status=400)

    if _claimed_today(request):
        return JsonResponse({
            'ok': False,
            'message': 'Hadiah hari ini sudah diklaim.',
        }, status=400)

    from gamification import services as game

    ok, message = game.claim_streak_freeze(request.user, today=today)

    if not ok:
        return JsonResponse({
            'ok': False,
            'message': message,
        }, status=400)

    request.session[FREEZE_SESSION_KEY] = today.isoformat()

    profile = game.get_profile(request.user)

    return JsonResponse({
        'ok': True,
        'freezes': profile.streak_freezes,
    })




@login_required
def weekly_report_view(request):
    return render(request, 'coming_soon.html', {
        'title': 'Ringkasan Mingguan',
        'icon': 'log',
        'description': 'Rekap CO₂, perbandingan minggu lalu, dan proyeksi tahunan.',
    })


@login_required
def api_daily_challenges(request):
    return JsonResponse({"status": "coming soon"})


@login_required
def api_challenge_data(request):
    user = request.user
    today = timezone.localdate()
    week_start = today - timedelta(days=6)

    logs_today = FoodLog.objects.filter(
        user=user,
        scanned_at__date=today,
    )

    weekly_logs = FoodLog.objects.filter(
        user=user,
        scanned_at__date__gte=week_start,
        scanned_at__date__lte=today,
    )

    budget = CarbonBudget.objects.filter(
        user=user,
        date=today,
    ).first()

    daily_grams = sum(log.co2_grams for log in logs_today)
    weekly_grams = sum(log.co2_grams for log in weekly_logs)

    daily_logs = list(logs_today)

    return JsonResponse({
        "user": {
            "id": user.id,
            "name": user.username,
        },
        "scans_today": len(daily_logs),
        "total_scans": FoodLog.objects.filter(user=user).count(),
        "daily_co2_kg": round(daily_grams / 1000, 2),
        "weekly_co2_kg": round(weekly_grams / 1000, 2),
        "daily_budget_kg": round(
            (budget.budget_grams if budget else 2000) / 1000, 2
        ),
        "weekly": [
            {
                "day": (week_start + timedelta(days=i)).strftime("%a"),
                "co2_kg": round(sum(
                    log.co2_grams
                    for log in weekly_logs
                    if timezone.localtime(log.scanned_at).date()
                    == week_start + timedelta(days=i)
                ) / 1000, 2),
            }
            for i in range(7)
        ],
    })


AVATAR_COUNT = 140  # 100 avatar spesies + 40 avatar spesial (lihat avatar-data.js)


@login_required
@require_POST
def save_profile_view(request):
    """Simpan avatar, nama tampilan, dan bio dalam satu request."""
    try:
        data = json.loads(request.body or b'{}')
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'message': 'Data tidak valid.'}, status=400)

    name = str(data.get('name', '')).strip()
    bio = str(data.get('bio', '')).strip()
    avatar = data.get('avatar')

    if isinstance(avatar, bool) or not isinstance(avatar, int) or not 0 <= avatar < AVATAR_COUNT:
        return JsonResponse({'ok': False, 'message': 'Avatar tidak valid.'}, status=400)
    if len(name) > 24:
        return JsonResponse({'ok': False, 'message': 'Nama maksimal 24 karakter.'}, status=400)
    if len(bio) > 80:
        return JsonResponse({'ok': False, 'message': 'Bio maksimal 80 karakter.'}, status=400)

    profile, _ = ChallengeProfile.objects.get_or_create(user=request.user)
    profile.display_name = name
    profile.bio = bio
    profile.avatar_id = avatar
    profile.save()

    return JsonResponse({'ok': True, 'name': name, 'bio': bio, 'avatar': avatar})