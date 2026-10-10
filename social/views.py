from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .community import nearest_canteens
from .forms import CampusForm
from .models import Canteen, CampusMembership
from .services import canteen_pins, canteen_posts, month_start, ranked_campuses, ranked_users, week_start


def leaderboard_view(request):
    tab = request.GET.get('tab', 'national')
    users = ranked_users(week_start())
    need_login = need_campus = False

    if tab == 'campus':
        if not request.user.is_authenticated:
            need_login, users = True, users.none()
        elif not hasattr(request.user, 'campus'):
            need_campus, users = True, users.none()
        else:
            users = users.filter(campus__university=request.user.campus.university)
    elif tab == 'friends':
        users = users.none()  # menunggu friend system dari modul Nasywa

    ranking = list(users[:50])
    return render(request, 'social/leaderboard.html', {
        'tab': tab,
        'ranking': ranking,
        'need_login': need_login,
        'need_campus': need_campus,
    })


def campus_war_view(request):
    campuses = ranked_campuses(month_start())
    my_campus = None
    if request.user.is_authenticated and hasattr(request.user, 'campus'):
        my_campus = request.user.campus.university
    return render(request, 'social/campus_war.html', {
        'campuses': campuses,
        'my_campus': my_campus,
    })


@login_required
def choose_campus_view(request):
    instance = CampusMembership.objects.filter(user=request.user).first()
    form = CampusForm(request.POST or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        membership = form.save(commit=False)
        membership.user = request.user
        membership.save()
        return redirect('social:campus_war')
    return render(request, 'social/choose_campus.html', {'form': form})


# ---------- Community ----------

def community_map_view(request):
    faculties = Canteen.objects.filter(is_active=True).values_list('faculty', flat=True).distinct().order_by('faculty')
    return render(request, 'social/community_map.html', {'faculties': list(faculties)})


def api_canteens(request):
    range_key = request.GET.get('range', 'today')
    if range_key not in ('today', 'week', 'all'):
        range_key = 'today'
    faculty = request.GET.get('faculty', '')
    return JsonResponse({'range': range_key, 'canteens': canteen_pins(range_key, faculty)})


def api_canteen_posts(request, pk):
    canteen = get_object_or_404(Canteen, pk=pk, is_active=True)
    range_key = request.GET.get('range', 'today')
    if range_key not in ('today', 'week', 'all'):
        range_key = 'today'
    try:
        page = max(1, int(request.GET.get('page', 1)))
    except ValueError:
        page = 1
    return JsonResponse(canteen_posts(canteen, range_key, page))


@require_POST
def api_nearest(request):
    """Terima lat/lng dari browser, balas 3 kantin terdekat. Koordinat tidak disimpan."""
    try:
        lat = float(request.POST['lat'])
        lng = float(request.POST['lng'])
    except (KeyError, ValueError):
        return JsonResponse({'error': 'lat dan lng wajib berupa angka'}, status=400)
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return JsonResponse({'error': 'koordinat tidak valid'}, status=400)
    try:
        accuracy = float(request.POST.get('accuracy', ''))
    except ValueError:
        accuracy = None
    return JsonResponse(nearest_canteens(lat, lng, accuracy))


def friends_view(request):
    return render(request, 'coming_soon.html', {
        'title': 'Teman',
        'icon': 'user',
        'description': 'Tambah teman dan lihat progres mereka di sini.',
    })


def challenge_view(request, pk):
    return render(request, 'coming_soon.html', {
        'title': 'Tantangan 1v1',
        'icon': 'fire',
        'description': 'Tantang temanmu dan lihat siapa yang paling hijau.',
    })
