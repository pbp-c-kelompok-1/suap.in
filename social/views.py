from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import F, Q
from django.db.models.functions import Coalesce
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .community import nearest_canteens
from .forms import CampusForm
from .friends import FriendshipError, friend_ids, relation_status, remove, respond, send_request
from .models import Canteen, CampusMembership, Friendship
from .services import canteen_pins, canteen_posts, month_start, ranked_campuses, scope_ranking, users_with_xp


def leaderboard_view(request):
    """Leaderboard sepanjang waktu (total XP dari modul gamification).

    Leaderboard mingguan ada di halaman Laporan (modul challenge) dan memakai
    sumber XP yang sama lewat social.services.users_with_xp(since=...).
    """
    tab = request.GET.get('tab', 'national')
    if tab not in ('friends', 'campus', 'national'):
        tab = 'national'
    users, reason = scope_ranking(users_with_xp(), request.user, tab)
    return render(request, 'social/leaderboard.html', {
        'tab': tab,
        'ranking': list(users[:50]),
        'need_login': reason == 'login',
        'need_campus': reason == 'campus',
        'no_friends': reason == 'no_friends',
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


SEARCH_LIMIT = 10


def is_ajax(request):
    return request.headers.get('x-requested-with') == 'fetch'


@login_required
def friends_view(request):
    """Read: daftar teman, permintaan masuk/keluar, dan cari user untuk ditambahkan."""
    me = request.user
    q = request.GET.get('q', '').strip()[:50]

    results = []
    if q:
        for u in User.objects.filter(username__icontains=q).exclude(pk=me.pk).order_by('username')[:SEARCH_LIMIT]:
            status, friendship = relation_status(me, u)
            results.append({'user': u, 'status': status, 'friendship': friendship})

    friends = (
        User.objects.filter(pk__in=friend_ids(me))
        .select_related('campus__university')
        .annotate(xp=Coalesce(F('game_profile__total_xp'), 0))
        .order_by('-xp', 'username')
    )
    friendships = {f.other(me).pk: f for f in Friendship.objects.filter(
        Q(from_user=me) | Q(to_user=me), status=Friendship.ACCEPTED)}
    friend_rows = [{'user': u, 'xp': u.xp, 'friendship': friendships.get(u.pk)} for u in friends]

    context = {
        'q': q,
        'results': results,
        'incoming': Friendship.objects.filter(to_user=me, status=Friendship.PENDING).select_related('from_user'),
        'outgoing': Friendship.objects.filter(from_user=me, status=Friendship.PENDING).select_related('to_user'),
        'friends': friend_rows,
    }
    template = 'social/partials/friends_region.html' if request.GET.get('partial') == '1' else 'social/friends.html'
    return render(request, template, context)


def friendship_action_response(request, func):
    """Jalankan aksi; balas JSON untuk AJAX, atau redirect + pesan untuk form biasa."""
    try:
        message, ok = func(), True
    except FriendshipError as exc:
        message, ok = str(exc), False
    if is_ajax(request):
        return JsonResponse({'ok': ok, 'message': message}, status=200 if ok else 400)
    (messages.success if ok else messages.error)(request, message)
    return redirect('social:friends')


@login_required
@require_POST
def friend_request_send(request):
    """Create: kirim permintaan pertemanan ke username tertentu."""
    receiver = get_object_or_404(User, username=request.POST.get('username', ''))
    return friendship_action_response(request, lambda: send_request(request.user, receiver))


@login_required
@require_POST
def friend_request_respond(request, pk):
    """Update: terima atau tolak permintaan yang masuk."""
    friendship = get_object_or_404(Friendship, pk=pk)
    accept = request.POST.get('action') == 'accept'
    return friendship_action_response(request, lambda: respond(friendship, request.user, accept))


@login_required
@require_POST
def friendship_delete(request, pk):
    """Delete: unfriend atau batalkan permintaan yang dikirim."""
    friendship = get_object_or_404(Friendship, pk=pk)
    return friendship_action_response(request, lambda: remove(friendship, request.user))


def challenge_view(request, pk):
    return render(request, 'coming_soon.html', {
        'title': 'Tantangan 1v1',
        'icon': 'fire',
        'description': 'Tantang temanmu dan lihat siapa yang paling hijau.',
    })
