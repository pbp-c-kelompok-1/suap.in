import base64
import math

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import FoodScanForm
from .models import CarbonBudget, FoodLog
from .services import (
    box_to_percent,
    calculate_carbon_analogy,
    detect_food_from_image,
    find_food_item,
    get_carbon_status,
    match_food_items_to_db,
)

SESSION_KEYS = ['scan_result', 'scan_raw', 'scan_photo', 'scan_photo_type']
BOX_COLORS = ['#ec4899', '#3b82f6', '#eab308', '#a855f7', '#f97316', '#22c55e']
MEAL_SLOTS = [
    ('sarapan', 'Sarapan', 'sunrise'),
    ('siang', 'Makan Siang', 'sun'),
    ('camilan', 'Camilan', 'snack'),
    ('malam', 'Makan Malam', 'moon'),
]
REQUIRED_SLOTS = {'sarapan', 'siang', 'malam'}
DEFAULT_BUDGET_GRAMS = 2000.0
MAX_ITEM_CO2 = 100000


def to_float(value):
    try:
        number = float(str(value).replace(',', '.'))
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def meal_slot_for(hour):
    if 4 <= hour < 10:
        return 'sarapan'
    if 10 <= hour < 15:
        return 'siang'
    if 15 <= hour < 18:
        return 'camilan'
    return 'malam'


def get_today_budget(user):
    budget, _ = CarbonBudget.objects.get_or_create(
        user=user,
        date=timezone.localdate(),
        defaults={'budget_grams': DEFAULT_BUDGET_GRAMS, 'used_grams': 0.0},
    )
    return budget


def collect_items(request, session_result):
    names = request.POST.getlist('item_name')
    co2_values = request.POST.getlist('item_co2')

    if names and len(names) == len(co2_values):
        raw_items = [{'name': n, 'co2_grams': c} for n, c in zip(names, co2_values)]
    else:
        raw_items = session_result.get('detected_items', [])

    items = []
    for raw in raw_items:
        name = str(raw.get('name', '')).strip()[:200]
        co2 = to_float(raw.get('co2_grams'))
        if not name or co2 is None or co2 < 0 or co2 > MAX_ITEM_CO2:
            continue
        items.append({'name': name, 'co2_grams': co2})
    return items


def scan_view(request):
    if request.method == 'POST':
        form = FoodScanForm(request.POST, request.FILES)
        if form.is_valid():
            photo = request.FILES['photo']
            content_type = photo.content_type or 'image/jpeg'

            result, raw_response = detect_food_from_image(photo, content_type)

            if result and 'detected_items' in result:
                request.session['scan_result'] = result
                request.session['scan_raw'] = raw_response

                photo.seek(0)
                photo_b64 = base64.b64encode(photo.read()).decode('utf-8')
                request.session['scan_photo'] = f"data:{content_type};base64,{photo_b64}"
                request.session['scan_photo_type'] = content_type

                return redirect('scanner:result')

            messages.error(request, 'Gagal mendeteksi makanan. Coba foto yang lebih jelas.')
        else:
            messages.error(request, 'File yang dipilih bukan gambar yang valid.')
    else:
        form = FoodScanForm()

    return render(request, 'scanner/scan.html', {'form': form})


@login_required
def result_view(request):
    result = request.session.get('scan_result')
    photo_b64 = request.session.get('scan_photo')

    if not result:
        messages.warning(request, 'Tidak ada hasil scan. Scan makanan dulu.')
        return redirect('scanner:scan')

    detected_items = result.get('detected_items', [])
    matched_items = match_food_items_to_db(detected_items)

    for index, match in enumerate(matched_items):
        box_style = box_to_percent(match['detected'].get('box'))
        match['box_style'] = box_style
        match['box_color'] = BOX_COLORS[index % len(BOX_COLORS)]
        match['label_above'] = bool(box_style) and float(box_style['top']) > 6
        match['co2'] = round(to_float(match['detected'].get('co2_grams')) or 0)
        match['name'] = str(match['detected'].get('name', '')).strip()

    total_co2 = sum(match['co2'] for match in matched_items)
    status_color, status_label = get_carbon_status(total_co2)

    context = {
        'result': result,
        'matched_items': matched_items,
        'total_co2': total_co2,
        'analogy': calculate_carbon_analogy(total_co2),
        'status_color': status_color,
        'status_label': status_label,
        'xp_earned': 10 + len(detected_items),
        'photo_b64': photo_b64,
        'alternative': result.get('alternative_suggestion', ''),
        'notes': result.get('notes', ''),
    }
    return render(request, 'scanner/result.html', context)


@login_required
@require_POST
def save_log_view(request):
    result = request.session.get('scan_result')

    if not result:
        messages.error(request, 'Tidak ada hasil scan untuk disimpan.')
        return redirect('scanner:scan')

    items = collect_items(request, result)
    if not items:
        messages.error(request, 'Tidak ada item valid untuk disimpan.')
        return redirect('scanner:result')

    raw_response = request.session.get('scan_raw', '')
    notes = result.get('notes', '')

    for item in items:
        FoodLog.objects.create(
            user=request.user,
            food_item=find_food_item(item['name']),
            custom_name=item['name'],
            co2_grams=item['co2_grams'],
            ai_raw_response=raw_response,
            notes=notes,
        )

    total_co2 = sum(item['co2_grams'] for item in items)
    budget = get_today_budget(request.user)
    budget.used_grams += total_co2
    budget.save()

    for key in SESSION_KEYS:
        request.session.pop(key, None)

    messages.success(request, f'Log tersimpan! Total {total_co2:.0f}g CO₂ ditambahkan ke hari ini.')
    return redirect('scanner:daily_log')


@login_required
def daily_log_view(request):
    today = timezone.localdate()
    logs = list(
        FoodLog.objects.filter(user=request.user, scanned_at__date=today)
        .select_related('food_item')
        .order_by('scanned_at')
    )

    grouped = {key: [] for key, _, _ in MEAL_SLOTS}
    for log in logs:
        log.display_name = log.custom_name or (log.food_item.name if log.food_item else 'Item')
        grouped[meal_slot_for(timezone.localtime(log.scanned_at).hour)].append(log)

    meals = []
    for key, label, icon in MEAL_SLOTS:
        entries = grouped[key]
        if not entries and key not in REQUIRED_SLOTS:
            continue
        meals.append({
            'key': key,
            'label': label,
            'icon': icon,
            'entries': entries,
            'summary': ', '.join(entry.display_name for entry in entries),
            'total': sum(entry.co2_grams for entry in entries),
        })

    budget = get_today_budget(request.user)
    status_color, status_label = get_carbon_status(budget.used_grams, budget.budget_grams)
    remaining = budget.remaining_grams

    context = {
        'meals': meals,
        'budget': budget,
        'remaining_grams': max(0, remaining),
        'over_grams': max(0, -remaining),
        'status_color': status_color,
        'status_label': status_label,
        'progress_percent': min(100, round(budget.percentage_used)),
        'today': today,
        'total_co2': budget.used_grams,
        'analogy': calculate_carbon_analogy(budget.used_grams),
    }
    return render(request, 'scanner/daily_log.html', context)


@login_required
@require_POST
def delete_log_view(request, log_id):
    log = get_object_or_404(FoodLog, id=log_id, user=request.user)

    budget = CarbonBudget.objects.filter(
        user=request.user,
        date=timezone.localtime(log.scanned_at).date(),
    ).first()
    if budget:
        budget.used_grams = max(0, budget.used_grams - log.co2_grams)
        budget.save()

    log.delete()
    messages.success(request, 'Entry log dihapus.')
    return redirect('scanner:daily_log')


def api_scan_status(request):
    return JsonResponse({'has_result': 'scan_result' in request.session})
