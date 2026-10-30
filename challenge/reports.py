"""Riwayat laporan mingguan.

Dihitung langsung dari FoodLog (tidak ada tabel snapshot), jadi tidak bisa tidak
sinkron dengan data scan. Dimulai dari minggu saat akun dibuat dan hanya memuat
minggu yang SUDAH selesai (Senin-Minggu). Yang ditampilkan dibatasi
REPORT_HISTORY_WEEKS minggu terakhir; data lebih lama tetap ada di database.
"""
from datetime import timedelta

from django.utils import timezone

from scanner.models import CarbonBudget, FoodLog

from .ranking import weekly_positions
from .services import DAY_ABBR, DEFAULT_BUDGET_GRAMS

REPORT_HISTORY_WEEKS = 26  # sekitar 6 bulan
DAYS_IN_YEAR = 365


def _monday(day):
    return day - timedelta(days=day.weekday())


def _week_budget_g(monday, budgets):
    return sum(budgets.get(monday + timedelta(days=i), DEFAULT_BUDGET_GRAMS) for i in range(7))


def _day_cells(monday, days, budgets):
    """Tujuh hari (Sen-Min) untuk grafik batang kecil di detail laporan."""
    peak = max([g for g in days.values()] + [DEFAULT_BUDGET_GRAMS]) or 1
    cells = []
    for i in range(7):
        day = monday + timedelta(days=i)
        grams = days.get(day)
        budget = budgets.get(day, DEFAULT_BUDGET_GRAMS)
        cells.append({
            'label': DAY_ABBR[i],
            'has': grams is not None,
            'kg': round((grams or 0) / 1000, 1),
            'over': grams is not None and grams > budget,
            'h': max(6, round(grams / peak * 100)) if grams is not None else 0,
        })
    return cells


def build_report_history(user, today=None):
    today = today or timezone.localdate()
    cur_monday = _monday(today)
    joined = timezone.localtime(user.date_joined).date()

    oldest_allowed = cur_monday - timedelta(weeks=REPORT_HISTORY_WEEKS)
    first_monday = max(_monday(joined), oldest_allowed)
    last_monday = cur_monday - timedelta(weeks=1)

    empty = {
        'weeks': [], 'joined': joined, 'weeks_with_data': 0,
        'avg_day_kg': None, 'projection_kg': None, 'best': None,
        'limit_weeks': REPORT_HISTORY_WEEKS,
    }
    if first_monday > last_monday:
        return empty

    range_end = last_monday + timedelta(days=6)
    rows = FoodLog.objects.filter(
        user=user,
        scanned_at__date__gte=first_monday,
        scanned_at__date__lte=range_end,
    ).values_list('scanned_at', 'co2_grams', 'ai_raw_response')
    budgets = dict(
        CarbonBudget.objects.filter(
            user=user, date__gte=first_monday, date__lte=range_end,
        ).values_list('date', 'budget_grams')
    )

    # {senin: {hari: gram}}, {senin: set(foto)}, {senin: jumlah baris tanpa respons AI}
    per_day, photos, loose = {}, {}, {}
    for scanned_at, grams, raw in rows:
        day = timezone.localtime(scanned_at).date()
        monday = _monday(day)
        days = per_day.setdefault(monday, {})
        days[day] = days.get(day, 0) + (grams or 0)
        if raw:
            photos.setdefault(monday, set()).add(raw)
        else:
            loose[monday] = loose.get(monday, 0) + 1

    positions = weekly_positions(user, first_monday, range_end)

    weeks = []
    monday = first_monday
    while monday <= last_monday:
        days = per_day.get(monday, {})
        total_g = sum(days.values())
        n_days = len(days)
        over = sum(
            1 for d, g in days.items()
            if g > budgets.get(d, DEFAULT_BUDGET_GRAMS)
        )
        weeks.append({
            'start': monday,
            'end': monday + timedelta(days=6),
            'has_data': n_days > 0,
            'total_kg': round(total_g / 1000, 1),
            'days_logged': n_days,
            'avg_day_g': (total_g / n_days) if n_days else 0,
            'avg_day_kg': round(total_g / n_days / 1000, 1) if n_days else 0,
            'scans': len(photos.get(monday, ())) + loose.get(monday, 0),
            'over_days': over,
            'delta_percent': None,
            'delta_abs': None,
            'bar': 0,
            'rank': positions.get(monday),
            'days': _day_cells(monday, days, budgets),
            'budget_kg': round(_week_budget_g(monday, budgets) / 7000, 1),
        })
        monday += timedelta(weeks=1)

    # Perubahan dibanding minggu bermakna sebelumnya (rata-rata per hari yang discan).
    prev = None
    for w in weeks:
        if w['has_data']:
            if prev and prev['avg_day_g'] > 0:
                w['delta_percent'] = round((w['avg_day_g'] - prev['avg_day_g']) / prev['avg_day_g'] * 100)
                w['delta_abs'] = abs(w['delta_percent'])
            prev = w

    peak = max((w['total_kg'] for w in weeks), default=0) or 1
    for w in weeks:
        w['bar'] = max(6, round(w['total_kg'] / peak * 100)) if w['has_data'] else 0

    with_data = [w for w in weeks if w['has_data']]
    avg_day_g = (sum(w['avg_day_g'] for w in with_data) / len(with_data)) if with_data else None
    best = min(with_data, key=lambda w: w['avg_day_g']) if with_data else None

    return {
        'weeks': list(reversed(weeks)),   # terbaru dulu
        'joined': joined,
        'weeks_with_data': len(with_data),
        'avg_day_kg': round(avg_day_g / 1000, 1) if avg_day_g is not None else None,
        'projection_kg': round(avg_day_g / 1000 * DAYS_IN_YEAR) if avg_day_g is not None else None,
        'best': best,
        'limit_weeks': REPORT_HISTORY_WEEKS,
    }
