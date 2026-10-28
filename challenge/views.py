import json
from datetime import timedelta

from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from scanner.models import CarbonBudget, FoodLog
from social.services import scope_ranking, users_with_xp

DAY_ABBR = ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min']
DEFAULT_BUDGET_GRAMS = 2000.0


def week_totals_by_day(user, week_start, week_end):
    logs = FoodLog.objects.filter(
        user=user,
        scanned_at__date__gte=week_start,
        scanned_at__date__lte=week_end,
    )
    totals = {}
    for log in logs:
        d = timezone.localtime(log.scanned_at).date()
        totals[d] = totals.get(d, 0.0) + log.co2_grams
    return totals


def challenge_list_view(request):
    context = {}
    if request.user.is_authenticated:
        today = timezone.localdate()
        week_start = today - timedelta(days=6)
        prev_week_start = week_start - timedelta(days=7)
        prev_week_end = week_start - timedelta(days=1)

        totals_by_date = week_totals_by_day(request.user, week_start, today)
        prev_totals_by_date = week_totals_by_day(request.user, prev_week_start, prev_week_end)

        weekly = []
        for i in range(7):
            d = week_start + timedelta(days=i)
            grams = totals_by_date.get(d, 0.0)
            weekly.append({
                'd': DAY_ABBR[d.weekday()],
                'v': round(grams / 1000, 2),
                'hasData': d in totals_by_date,
            })

        this_week_kg = round(sum(totals_by_date.values()) / 1000, 2)
        prev_week_kg = round(sum(prev_totals_by_date.values()) / 1000, 2)
        has_this_week_data = bool(totals_by_date)
        has_prev_week_data = bool(prev_totals_by_date)

        delta_percent = None
        if has_this_week_data and has_prev_week_data and prev_week_kg > 0:
            delta_percent = round((this_week_kg - prev_week_kg) / prev_week_kg * 100)

        projection_kg = None
        savings_kg = None
        savings_trees = None
        is_saving = None
        if has_this_week_data:
            projection_kg = round(this_week_kg / 7 * 365)
            if has_prev_week_data:
                diff_kg = prev_week_kg - this_week_kg
                is_saving = diff_kg > 0
                savings_kg = round(abs(diff_kg) * 52)
                savings_trees = round(savings_kg / 21)

        budget = CarbonBudget.objects.filter(user=request.user, date=today).first()
        budget_cap_kg = round((budget.budget_grams if budget else DEFAULT_BUDGET_GRAMS) / 1000, 2)

        # Peringkat mingguan = XP yang didapat 7 hari terakhir (periode yang sama dengan laporan ini).
        # Sumber XP sama dengan leaderboard sepanjang waktu di modul social.
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
            'week_end': today,
            'weekly_json': json.dumps(weekly),
            'rank_json': json.dumps(ranking),
            'budget_cap_kg': budget_cap_kg,
            'budget_cap_kg_js': f'{budget_cap_kg:.2f}',
            'this_week_kg': this_week_kg,
            'prev_week_kg': prev_week_kg,
            'has_prev_week_data': has_prev_week_data,
            'delta_percent': delta_percent,
            'projection_kg': projection_kg,
            'savings_kg': savings_kg,
            'savings_trees': savings_trees,
            'is_saving': is_saving,
        }
    return render(request, 'challenge/dashboard.html', context)


def weekly_report_view(request):
    return render(request, 'coming_soon.html', {
        'title': 'Ringkasan Mingguan',
        'icon': 'log',
        'description': 'Rekap CO₂, perbandingan minggu lalu, dan proyeksi tahunan.',
    })


def api_daily_challenges(request):
    return JsonResponse({"status": "coming soon"})
