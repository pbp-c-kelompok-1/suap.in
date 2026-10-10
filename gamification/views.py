from datetime import timedelta

from django.shortcuts import render
from django.utils import timezone

from gamification.models import GameProfile
from scanner.models import CarbonBudget, FoodLog
from scanner.services import calculate_carbon_analogy, get_carbon_status


MILESTONES = [3, 7, 14, 30]
DAY_ABBR = ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min']
STATE_LABEL = {'done': 'ada scan', 'missed': 'terlewat', 'freeze': 'freeze', 'empty_day': 'belum'}


def dashboard_view(request):
    context = {}
    if request.user.is_authenticated:
        budget = CarbonBudget.objects.filter(user=request.user, date=timezone.localdate()).first()
        used = budget.used_grams if budget else 0.0
        limit = budget.budget_grams if budget else 2000.0
        status_color, status_label = get_carbon_status(used, limit)
        recent = list(
            FoodLog.objects.filter(user=request.user)
            .select_related('food_item')
            .order_by('-scanned_at')[:4]
        )
        for log in recent:
            log.display_name = log.custom_name or (log.food_item.name if log.food_item else 'Item')

        context = {
            'used_grams': used,
            'limit_grams': limit,
            'remaining_grams': max(0, limit - used),
            'over_grams': max(0, used - limit),
            'progress_percent': min(100, round(used / limit * 100)) if limit else 0,
            'status_color': status_color,
            'status_label': status_label,
            'analogy': calculate_carbon_analogy(used),
            'recent_logs': recent,
        }
    return render(request, 'gamification/dashboard.html', context)


def streak_view(request):
    context = {}
    if request.user.is_authenticated:
        gp, _ = GameProfile.objects.get_or_create(user=request.user)
        today = timezone.localdate()
        start = today - timedelta(days=6)
        scanned = {timezone.localtime(l.scanned_at).date()
                   for l in FoodLog.objects.filter(user=request.user, scanned_at__date__gte=start)}
        week = []
        for i in range(7):
            d = start + timedelta(days=i)
            state = 'done' if d in scanned else ('missed' if d < today else 'empty_day')
            week.append({'label': DAY_ABBR[d.weekday()], 'state': state,
                         'state_label': STATE_LABEL[state], 'is_today': d == today})

        next_goal = next((m for m in MILESTONES if m > gp.current_streak), MILESTONES[-1])
        context = {
            'streak': gp.current_streak,
            'record': gp.record_streak,
            'freezes': gp.streak_freezes,
            'scanned_today': today in scanned,
            'week': week,
            'week_done': sum(1 for w in week if w['state'] == 'done'),
            'next_goal': next_goal,
            'goal_percent': min(100, round(gp.current_streak / next_goal * 100)),
            'days_left': max(0, next_goal - gp.current_streak),
            'milestones': [{'days': m, 'reached': gp.record_streak >= m} for m in MILESTONES],
            'reached_count': sum(1 for m in MILESTONES if gp.record_streak >= m),
        }
    return render(request, 'gamification/streak.html', context)


def level_view(request):
    context = {
        'title': 'Level & XP',
        'icon': 'sparkle',
        'description': 'Lihat progres XP, tier level, dan koleksi lencanamu.',
    }
    if request.user.is_authenticated:
        profile, _ = GameProfile.objects.get_or_create(user=request.user)
        context['profile'] = profile
    return render(request, 'coming_soon.html', context)
