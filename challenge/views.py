import json
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from scanner.models import FoodLog, CarbonBudget
from story.models import FriendChallenge

from .duels import decline_duel
from .models import ChallengeProfile, Notification, QuestClaim
from .reports import build_report_history
from .services import (
    DEFAULT_BUDGET_GRAMS,
    DEFAULT_QUEST_XP,
    build_challenge_data,
    count_scans,
    kg,
    saved_today_grams,
    serialize_notification,
    todays_quests,
    week_totals_by_day,
)

DAYS_IN_YEAR = 365
KG_PER_TREE_PER_YEAR = 21   # kira-kira CO2 yang diserap satu pohon dalam setahun
MIN_DAYS_FOR_GOOD_PROJECTION = 3

FREEZE_SESSION_KEY = 'challenge_freeze_claimed_on'


def _claimed_today(request):
    return request.session.get(FREEZE_SESSION_KEY) == timezone.localdate().isoformat()


@login_required
def challenge_list_view(request):
    today = timezone.localdate()

    # Satu minggu = Senin sampai Minggu, sama dengan peringkat mingguan.
    # Rentang tanggal tetap sepanjang minggu dan baru berganti hari Senin.
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    prev_week_start = week_start - timedelta(days=7)
    prev_week_end = week_start - timedelta(days=1)

    totals_by_date = week_totals_by_day(request.user, week_start, today)
    prev_totals_by_date = week_totals_by_day(
        request.user,
        prev_week_start,
        prev_week_end,
    )

    this_week_g = sum(totals_by_date.values())
    prev_week_g = sum(prev_totals_by_date.values())
    this_week_kg = round(this_week_g / 1000, 2)
    prev_week_kg = round(prev_week_g / 1000, 2)

    days_logged = len(totals_by_date)
    prev_days_logged = len(prev_totals_by_date)
    has_this_week_data = days_logged > 0
    has_prev_week_data = prev_days_logged > 0

    # Minggu ini belum selesai, jadi dibandingkan lewat RATA-RATA PER HARI
    # (hari yang ada scan-nya), bukan total. Kalau tidak, minggu berjalan
    # selalu terlihat "jauh lebih hemat" hanya karena harinya belum lengkap.
    this_avg_g = this_week_g / days_logged if has_this_week_data else 0
    prev_avg_g = prev_week_g / prev_days_logged if has_prev_week_data else 0

    delta_percent = None
    if has_this_week_data and has_prev_week_data and prev_avg_g > 0:
        delta_percent = round((this_avg_g - prev_avg_g) / prev_avg_g * 100)

    budget_row = CarbonBudget.objects.filter(user=request.user, date=today).first()
    budget_day_g = budget_row.budget_grams if budget_row else DEFAULT_BUDGET_GRAMS

    projection = None
    if has_this_week_data:
        projection_kg = round(this_avg_g / 1000 * DAYS_IN_YEAR)
        budget_year_kg = round(budget_day_g / 1000 * DAYS_IN_YEAR)
        bar_max = max(projection_kg, budget_year_kg, 1)
        is_over_budget = projection_kg > budget_year_kg
        projection = {
            'kg': projection_kg,
            'daily_avg_kg': round(this_avg_g / 1000, 1),
            'days_logged': days_logged,
            'budget_day_kg': round(budget_day_g / 1000, 1),
            'budget_year_kg': budget_year_kg,
            'bar_mine': round(projection_kg / bar_max * 100),
            'bar_budget': round(budget_year_kg / bar_max * 100),
            'is_over_budget': is_over_budget,
            'gap_kg': abs(budget_year_kg - projection_kg),
            'gap_percent': (
                round(abs(budget_year_kg - projection_kg) / budget_year_kg * 100)
                if budget_year_kg else 0
            ),
            'low_confidence': days_logged < MIN_DAYS_FOR_GOOD_PROJECTION,
        }

    savings_kg = savings_trees = is_saving = None
    if has_this_week_data and has_prev_week_data:
        diff_g_per_day = prev_avg_g - this_avg_g
        is_saving = diff_g_per_day > 0
        savings_kg = round(abs(diff_g_per_day) / 1000 * DAYS_IN_YEAR)
        savings_trees = round(savings_kg / KG_PER_TREE_PER_YEAR)

    from social.services import scope_ranking, users_with_xp
    weekly_xp = users_with_xp(since=week_start)
    ranking = {}
    for key, scope in (('teman', 'friends'), ('kampus', 'campus'), ('nasional', 'national')):
        users, reason = scope_ranking(weekly_xp, request.user, scope)
        rows = [{'name': u.username, 'xp': u.xp, 'is_me': u.pk == request.user.pk} for u in users[:20]]
        if reason != 'campus' and not any(r['is_me'] for r in rows):
            rows.append({'name': request.user.username, 'xp': 0, 'is_me': True})
        ranking[key] = rows

    context = {
        'week_start': week_start,
        'week_end': week_end,
        'this_week_kg': this_week_kg,
        'prev_week_kg': prev_week_kg,
        'prev_avg_kg': round(prev_avg_g / 1000, 1),
        'has_prev_week_data': has_prev_week_data,
        'delta_percent': delta_percent,
        'delta_abs': abs(delta_percent) if delta_percent is not None else None,
        'projection': projection,
        'savings_kg': savings_kg,
        'savings_trees': savings_trees,
        'is_saving': is_saving,
        'history': build_report_history(request.user, today),
        'challenge_data': build_challenge_data(
            request.user,
            claimed_today=_claimed_today(request),
        ),
        'rank_json': json.dumps(ranking),
    }

    return render(request, 'challenge/dashboard.html', context)


@login_required
def api_stats_view(request):
    """Angka 'hemat dari budget' hari ini (berubah tiap scan)."""
    today = timezone.localdate()
    return JsonResponse({'ok': True, 'avoidedKg': kg(saved_today_grams(request.user, today))})


@login_required
@require_POST
def claim_freeze_view(request):
    """Klaim streak freeze setelah semua misi selesai."""
    today = timezone.localdate()

    quests, _, _, _ = todays_quests(request.user, today)

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

    ok, message = game.claim_streak_freeze(
        request.user,
        today=today,
    )

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


def _json_body(request):
    try:
        data = json.loads(request.body or b'{}')
    except (ValueError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


@login_required
@require_POST
def claim_quest_view(request):
    """Klaim hadiah XP satu misi yang sudah selesai (manual oleh user)."""
    data = _json_body(request)
    if data is None:
        return JsonResponse({'ok': False, 'message': 'Data tidak valid.'}, status=400)

    quest_id = str(data.get('quest_id', ''))[:40]
    today = timezone.localdate()

    quests, _, _, _ = todays_quests(request.user, today)
    quest = next((q for q in quests if q['id'] == quest_id), None)

    if quest is None:
        return JsonResponse({'ok': False, 'message': 'Misi tidak ditemukan.'}, status=404)

    if quest['val'] < quest['goal']:
        return JsonResponse({'ok': False, 'message': 'Misi ini belum selesai.'}, status=400)

    from gamification import services as game

    xp = quest.get('xp', DEFAULT_QUEST_XP)

    try:
        with transaction.atomic():
            QuestClaim.objects.create(
                user=request.user, date=today, quest_id=quest_id, xp=xp,
            )
            result = game.award_xp(request.user, xp)
    except IntegrityError:
        return JsonResponse({
            'ok': False,
            'message': 'Hadiah misi ini sudah diklaim.',
        }, status=400)

    # Ubah notifikasi "klaim hadiahmu" jadi konfirmasi, dan tandai sudah dibaca.
    key = f"quest-{today.isoformat()}-{quest_id}"
    Notification.objects.filter(user=request.user, key=key).update(
        icon='check',
        tone='green',
        title='Hadiah misi diklaim!',
        body=f"{quest['title']}: kamu mendapat +{xp} XP.",
        read_at=timezone.now(),
    )
    notif = Notification.objects.filter(
        user=request.user, key=key, dismissed=False,
    ).first()

    profile = game.get_profile(request.user)
    prog = game.xp_progress(profile)

    return JsonResponse({
        'ok': True,
        'quest_id': quest_id,
        'xp': xp,
        'level': profile.level,
        'leveledUp': result['leveled_up'],
        'tier': game.tier_from_level(profile.level),
        'xpCurrent': prog['current'],
        'cap': prog['needed'],
        'notif': serialize_notification(notif) if notif else None,
    })


@login_required
@require_POST
def notifications_read_view(request):
    """Tandai notifikasi sudah dibaca: {"ids": ["..."]} atau {"all": true}."""
    data = _json_body(request)
    if data is None:
        return JsonResponse({'ok': False, 'message': 'Data tidak valid.'}, status=400)

    qs = Notification.objects.filter(
        user=request.user, dismissed=False, read_at__isnull=True,
    )
    if not data.get('all'):
        ids = data.get('ids')
        if not isinstance(ids, list):
            return JsonResponse({'ok': False, 'message': 'Data tidak valid.'}, status=400)
        qs = qs.filter(key__in=[str(i)[:80] for i in ids[:200]])

    updated = qs.update(read_at=timezone.now())
    return JsonResponse({'ok': True, 'updated': updated})


@login_required
@require_POST
def notification_dismiss_view(request):
    """Hapus notifikasi dari daftar: {"id": "..."}."""
    data = _json_body(request)
    key = str((data or {}).get('id', ''))[:80]
    if not key:
        return JsonResponse({'ok': False, 'message': 'Data tidak valid.'}, status=400)

    Notification.objects.filter(user=request.user, key=key).update(dismissed=True)
    return JsonResponse({'ok': True})


@login_required
def weekly_report_view(request):
    return redirect(f"{reverse('challenge:list')}#/laporan")


@login_required
def api_daily_challenges(request):
    today = timezone.localdate()

    quests, scans_today, used_grams, budget_grams = todays_quests(
        request.user,
        today,
    )

    return JsonResponse({
        "date": today.isoformat(),
        "quests": quests,
        "scans_today": scans_today,
        "used_grams": used_grams,
        "budget_grams": budget_grams,
    })


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
        "scans_today": count_scans(logs_today),
        "total_scans": count_scans(FoodLog.objects.filter(user=user)),
        "daily_co2_kg": round(daily_grams / 1000, 2),
        "weekly_co2_kg": round(weekly_grams / 1000, 2),
        "daily_budget_kg": round(
            (budget.budget_grams if budget else 2000) / 1000,
            2,
        ),
        "weekly": [
            {
                "day": (
                    week_start + timedelta(days=i)
                ).strftime("%a"),
                "co2_kg": round(
                    sum(
                        log.co2_grams
                        for log in weekly_logs
                        if timezone.localtime(log.scanned_at).date()
                        == week_start + timedelta(days=i)
                    ) / 1000,
                    2,
                ),
            }
            for i in range(7)
        ],
    })


AVATAR_COUNT = 140


@login_required
@require_POST
def save_profile_view(request):
    """Simpan avatar, nama tampilan, dan bio."""
    try:
        data = json.loads(request.body or b'{}')
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({
            'ok': False,
            'message': 'Data tidak valid.',
        }, status=400)

    name = str(data.get('name', '')).strip()
    bio = str(data.get('bio', '')).strip()
    avatar = data.get('avatar')

    if (
        isinstance(avatar, bool)
        or not isinstance(avatar, int)
        or not 0 <= avatar < AVATAR_COUNT
    ):
        return JsonResponse({
            'ok': False,
            'message': 'Avatar tidak valid.',
        }, status=400)

    if len(name) > 24:
        return JsonResponse({
            'ok': False,
            'message': 'Nama maksimal 24 karakter.',
        }, status=400)

    if len(bio) > 80:
        return JsonResponse({
            'ok': False,
            'message': 'Bio maksimal 80 karakter.',
        }, status=400)

    profile, _ = ChallengeProfile.objects.get_or_create(
        user=request.user,
    )

    profile.display_name = name
    profile.bio = bio
    profile.avatar_id = avatar
    profile.save()

    return JsonResponse({
        'ok': True,
        'name': name,
        'bio': bio,
        'avatar': avatar,
    })


@login_required
@require_POST
def decline_duel_view(request, pk):
    """Tolak tantangan dari notifikasi. Hanya penerima yang boleh (selain itu 403)."""
    try:
        decline_duel(request.user, pk)
    except FriendChallenge.DoesNotExist:
        raise Http404('Tantangan tidak ditemukan.')
    except ValidationError as exc:
        return JsonResponse({'ok': False, 'message': ' '.join(exc.messages)}, status=409)
    return JsonResponse({'ok': True, 'message': 'Tantangan ditolak.'})
