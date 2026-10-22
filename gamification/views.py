from django.http import JsonResponse
from django.shortcuts import render

from scanner.models import CarbonBudget, FoodLog
from scanner.services import calculate_carbon_analogy, get_carbon_status

from .services import *

from gamification.models import GameProfile, UserBadge, Badge
from datetime import timedelta
import json
from django.utils import timezone
from scanner.models import FoodLog
from .models import GameProfile


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



DAY_ABBR = ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min']
STATE_LABEL = {'done': 'ada scan', 'missed': 'terlewat', 'freeze': 'freeze', 'empty_day': 'belum'}

def streak_view(request):
    context = {}
    if request.user.is_authenticated:
        gp, _ = GameProfile.objects.get_or_create(user=request.user)
        today = timezone.localdate()
        start = today - timedelta(days=today.weekday())
        scanned = {timezone.localtime(l.scanned_at).date()
                   for l in FoodLog.objects.filter(user=request.user, scanned_at__date__gte=start)}
        week = []
        for i in range(7):
            d = start + timedelta(days=i)
            state = 'done' if d in scanned else ('missed' if d < today else 'empty_day')
            week.append({'label': DAY_ABBR[d.weekday()], 'state': state,
                         'state_label': STATE_LABEL[state], 'is_today': d == today})
        
        # To mark freeze days, store used freeze dates and set state='freeze' for them.
        next_goal = next((m for m in STREAK_MILESTONES if m > (gp.current_streak % 360)), STREAK_MILESTONES[-1])
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
            'milestones': [{'days': m, 'reached': gp.record_streak >= m} for m in STREAK_MILESTONES],
            'reached_count': sum(1 for m in STREAK_MILESTONES if gp.record_streak >= m),
        }
        check_badges(request.user)
    return render(request, 'gamification/streak.html', context)


TIER_STYLE = [('teal', 'leaf'), ('green', 'sprout'), ('greenish-yellow', 'tree'), ('amber', 'globe')]
MISSION_XP = 25  # rata-rata XP misi harian (misi.js: 20-30)

def level_view(request):
    context = {}
    if request.user.is_authenticated:
        profile = get_profile(request.user)
        level = profile.level
        tiers = []
        for i, (min_level, name) in enumerate(TIERS):
            max_level = TIERS[i + 1][0] - 1 if i + 1 < len(TIERS) else None
            span_end = (max_level or MAX_LEVEL) + 1
            if max_level is not None and level > max_level:
                state, percent = 'reached', 100
            elif level >= min_level:
                state = 'current'
                percent = min(100, round((level - min_level) / (span_end - min_level) * 100))
            else:
                state, percent = 'locked', 0
            tone, icon = TIER_STYLE[i % len(TIER_STYLE)]
            tiers.append({
                'name': name, 'min_level': min_level, 'max_level': max_level,
                'state': state, 'percent': percent, 'tone': tone, 'icon': icon,
                'levels_left': max(0, min_level - level),
            })
        is_max = level >= MAX_LEVEL
        progress = xp_progress(profile)
        context = {
            'level': level, 'tier_name': tier_from_level(level), 'total_xp': profile.total_xp,
            'progress': progress, 'is_max_level': is_max, 'next_level': level + 1,
            'xp_to_next': 0 if is_max else progress['needed'] - progress['current'],
            'tiers': tiers, 'reached_count': sum(1 for t in tiers if t['state'] != 'locked'),
            'mission_xp': MISSION_XP,
        }
    return render(request, 'gamification/level.html', context)

def get_badge_json(request):
    seedBadges()
    check_badges(request.user)
    user_badges = UserBadge.objects.filter(user=request.user)

    data = []
    for user_badge in user_badges:
        badge = user_badge.badge
        data.append({
            'code': badge.code,
            'fields': {
                'name': badge.name,
                'description': badge.description,
                'icon': badge.icon,
                'earned_at': user_badge.earned_at.strftime("%d %b %Y"),
                'material': badge_material_from_threshold(badge.criteria_type, badge.threshold)
            }
        })

    return JsonResponse(data, safe=False)

def badges_view(request):
    context = {}
    if request.user.is_authenticated:
        check_badges(request.user)
        context = {
            'badge_count': len(json.loads(get_badge_json(request).content))
        }
    return render(request, 'gamification/badges.html', context)

def story_view(request):
    return render(request, 'coming_soon.html', {
        'title': 'Story',
        'icon': 'leaf',
        'description': 'Episode komik digital akan terbuka seiring naiknya levelmu.',
    })
