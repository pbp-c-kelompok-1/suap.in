from django.shortcuts import render
from django.utils import timezone

from scanner.models import CarbonBudget, FoodLog
from scanner.services import calculate_carbon_analogy, get_carbon_status


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
    return render(request, 'coming_soon.html', {
        'title': 'Streak',
        'icon': 'fire',
        'description': 'Pantau streak harianmu dan pakai streak freeze di sini.',
    })


def level_view(request):
    return render(request, 'coming_soon.html', {
        'title': 'Level & XP',
        'icon': 'sparkle',
        'description': 'Lihat progres XP, tier level, dan koleksi lencanamu.',
    })


def story_view(request):
    return render(request, 'coming_soon.html', {
        'title': 'Story',
        'icon': 'leaf',
        'description': 'Episode komik digital akan terbuka seiring naiknya levelmu.',
    })
