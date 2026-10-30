"""Pembuatan dan pembacaan snapshot laporan mingguan.

Setiap minggu yang sudah selesai disimpan sebagai WeeklyReport (Senin-Minggu).
Generator bersifat idempoten dan riwayat UI dibaca kembali dari snapshot database.
"""
from datetime import date, timedelta

from django.utils import timezone

from scanner.models import CarbonBudget, FoodLog

from .models import WeeklyReport

from .ranking import weekly_positions
from .services import DAY_ABBR, DEFAULT_BUDGET_GRAMS

REPORT_HISTORY_WEEKS = 26  # sekitar 6 bulan
DAYS_IN_YEAR = 365


def _monday(day):
    return day - timedelta(days=day.weekday())


def _week_budget_g(monday, budgets):
    return sum(budgets.get(monday + timedelta(days=i), DEFAULT_BUDGET_GRAMS) for i in range(7))


def _day_cells(monday, days, budgets, scans_by_day):
    """Tujuh hari (Sen-Min) untuk grafik batang kecil di detail laporan."""
    peak = max([g for g in days.values()] + [DEFAULT_BUDGET_GRAMS]) or 1
    cells = []
    for i in range(7):
        day = monday + timedelta(days=i)
        grams = days.get(day)
        budget = budgets.get(day, DEFAULT_BUDGET_GRAMS)
        cells.append({
            # Key utama sesuai kontrak template laporan.
            'date': day,
            'has_data': grams is not None,
            'total_kg': round((grams or 0) / 1000, 2),
            'scans': scans_by_day.get(day, 0),
            'budget_kg': round(budget / 1000, 1),
            'over_budget': grams is not None and grams > budget,
            'bar_height': max(6, round(grams / peak * 100)) if grams is not None else 0,
            'h': max(6, round(grams / peak * 100)) if grams is not None else 0,
            # Alias kompatibilitas untuk pemanggil lama.
            'label': DAY_ABBR[i], 'has': grams is not None,
            'kg': round((grams or 0) / 1000, 1),
            'over': grams is not None and grams > budget,
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

    expected_mondays = []
    cursor = first_monday
    while cursor <= last_monday:
        expected_mondays.append(cursor)
        cursor += timedelta(weeks=1)

    # Jika seluruh snapshot sudah ada, baca langsung dari database tanpa
    # mengagregasi ulang FoodLog atau menghitung ranking.
    existing = {r.week_start: r for r in WeeklyReport.objects.filter(
        user=user, week_start__gte=first_monday, week_start__lte=last_monday,
    )}
    if all(monday in existing for monday in expected_mondays):
        saved_weeks = []
        for monday in expected_mondays:
            record = existing[monday]
            payload = record.data or {}
            week = dict(payload)
            week['start'] = record.week_start
            week['end'] = record.week_end
            week['days'] = [dict(d, date=date.fromisoformat(d['date']))
                            for d in payload.get('days', [])]
            saved_weeks.append(week)
        with_data = [w for w in saved_weeks if w['has_data']]
        avg_day_g = (sum(w['avg_day_g'] for w in with_data) / len(with_data)) if with_data else None
        best = min(with_data, key=lambda w: w['avg_day_g']) if with_data else None
        return {
            'weeks': list(reversed(saved_weeks)), 'joined': joined,
            'weeks_with_data': len(with_data),
            'avg_day_kg': round(avg_day_g / 1000, 1) if avg_day_g is not None else None,
            'projection_kg': round(avg_day_g / 1000 * DAYS_IN_YEAR) if avg_day_g is not None else None,
            'best': best, 'limit_weeks': REPORT_HISTORY_WEEKS,
        }

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
    per_day, photos, loose, scans_by_day, photo_ids_by_day = {}, {}, {}, {}, {}
    for scanned_at, grams, raw in rows:
        day = timezone.localtime(scanned_at).date()
        monday = _monday(day)
        days = per_day.setdefault(monday, {})
        days[day] = days.get(day, 0) + (grams or 0)
        scans_by_day[day] = scans_by_day.get(day, 0) + (1 if not raw else 0)
        if raw:
            photos.setdefault(monday, set()).add(raw)
            photo_ids_by_day.setdefault(day, set()).add(raw)
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
            'total_grams': total_g,
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
            'days': _day_cells(monday, days, budgets, scans_by_day),
            'budget_kg': round(_week_budget_g(monday, budgets) / 7000, 1),
        })
        for cell in weeks[-1]['days']:
            cell['scans'] = scans_by_day.get(cell['date'], 0) + len(
                photo_ids_by_day.get(cell['date'], set())
            )
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

    # Simpan satu snapshot untuk setiap minggu yang sudah selesai. get_or_create
    # membuat proses ini aman dipanggil berulang dan menjaga laporan historis tetap. 
    for week in weeks:
        rank = week.get('rank') or {}
        payload = {
            'has_data': week['has_data'], 'total_grams': week['total_grams'],
            'total_kg': week['total_kg'], 'days_logged': week['days_logged'], 'avg_day_g': week['avg_day_g'],
            'avg_day_kg': week['avg_day_kg'], 'scans': week['scans'],
            'over_days': week['over_days'], 'delta_percent': week['delta_percent'],
            'delta_abs': week['delta_abs'], 'bar': week['bar'],
            'rank': rank, 'days': [dict(d, date=d['date'].isoformat()) for d in week['days']],
            'budget_kg': week['budget_kg'],
        }
        WeeklyReport.objects.get_or_create(
            user=user, week_start=week['start'],
            defaults={
                'week_end': week['end'],
                'total_co2_grams': week['total_grams'],
                'days_logged': week['days_logged'], 'scans': week['scans'],
                'average_daily_grams': week['avg_day_g'],
                'projection_annual_kg': (
                    round(week['avg_day_g'] / 1000 * DAYS_IN_YEAR)
                    if week['has_data'] else None
                ),
                'rank_national': rank.get('pos'),
                'rank_campus': rank.get('campus_pos'),
                'data': payload,
            },
        )

    # Baca kembali payload yang tersimpan: halaman riwayat memakai record WeeklyReport.
    saved = {r.week_start: r for r in WeeklyReport.objects.filter(
        user=user, week_start__gte=first_monday, week_start__lte=last_monday,
    )}
    for week in weeks:
        record = saved.get(week['start'])
        if not record:
            continue
        payload = record.data or {}
        week.update({k: v for k, v in payload.items() if k != 'days'})
        week['days'] = [dict(d, date=date.fromisoformat(d['date']))
                        for d in payload.get('days', [])]
        week['rank'] = payload.get('rank')

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
