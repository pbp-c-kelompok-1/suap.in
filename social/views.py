from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import F, Q
from django.db.models.functions import Coalesce
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .community import nearest_canteens
from .forms import CampusForm, FriendRequestForm, FriendResponseForm, first_error
from .friends import FriendshipError, friend_ids, relation_status, remove, respond, send_request
from .models import Canteen, CampusMembership, Friendship
from .ratelimit import rate_limit
from .services import canteen_pins, canteen_posts, month_start, ranked_campuses, scope_ranking, users_with_xp


def is_ajax(request):
    return request.headers.get('x-requested-with') == 'fetch'


def is_partial(request):
    return request.GET.get('partial') == '1'


LEADERBOARD_TABS = [('friends', 'Teman'), ('campus', 'Kampus'), ('national', 'Nasional')]


def leaderboard_view(request):
    """Leaderboard sepanjang waktu (total XP dari modul gamification).

    Leaderboard mingguan ada di halaman Laporan (modul challenge) dan memakai
    sumber XP yang sama lewat social.services.users_with_xp(since=...).
    ?partial=1 hanya merender daftar peringkat (dipakai saat ganti tab lewat AJAX).
    """
    tab = request.GET.get('tab', 'national')
    if tab not in dict(LEADERBOARD_TABS):
        tab = 'national'
    users, reason = scope_ranking(users_with_xp(), request.user, tab)
    template = 'social/partials/leaderboard_region.html' if is_partial(request) else 'social/leaderboard.html'
    return render(request, template, {
        'tab': tab,
        'tabs': LEADERBOARD_TABS,
        'ranking': list(users[:50]),
        'need_login': reason == 'login',
        'need_campus': reason == 'campus',
        'no_friends': reason == 'no_friends',
    })


def campus_war_view(request):
    membership = None
    if request.user.is_authenticated:
        membership = CampusMembership.objects.filter(user=request.user).select_related('university').first()
    template = 'social/partials/campus_war_region.html' if is_partial(request) else 'social/campus_war.html'
    return render(request, template, {
        'campuses': ranked_campuses(month_start()),
        'my_campus': membership.university if membership else None,
        'form': CampusForm(instance=membership),
    })


@login_required
@rate_limit('campus', limit=10, fallback='social:campus_war')
def choose_campus_view(request):
    """Create/Update CampusMembership. AJAX dibalas JSON, form biasa di-redirect."""
    instance = CampusMembership.objects.filter(user=request.user).first()
    form = CampusForm(request.POST or None, instance=instance)
    if request.method == 'POST':
        if form.is_valid():
            membership = form.save(commit=False)
            membership.user = request.user
            membership.save()
            message = f'Kampusmu sekarang {membership.university.short_name}.'
            if is_ajax(request):
                return JsonResponse({'ok': True, 'message': message, 'campus': membership.university.short_name})
            messages.success(request, message)
            return redirect('social:campus_war')
        if is_ajax(request):
            return JsonResponse({'ok': False, 'message': first_error(form)}, status=400)
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
@rate_limit('nearest', limit=20)
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
    template = 'social/partials/friends_region.html' if is_partial(request) else 'social/friends.html'
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


def form_action_response(request, form, action):
    """Validasi form dulu; kalau valid jalankan aksi, kalau tidak balas pesan error form."""
    def run():
        if not form.is_valid():
            raise FriendshipError(first_error(form))
        return action(form)
    return friendship_action_response(request, run)


@login_required
@require_POST
@rate_limit('friend_request', limit=10, fallback='social:friends')
def friend_request_send(request):
    """Create: kirim permintaan pertemanan ke username tertentu."""
    form = FriendRequestForm(request.POST, sender=request.user)
    return form_action_response(request, form, lambda f: send_request(request.user, f.receiver))


@login_required
@require_POST
@rate_limit('friend_action', limit=30, fallback='social:friends')
def friend_request_respond(request, pk):
    """Update: terima atau tolak permintaan yang masuk."""
    friendship = get_object_or_404(Friendship, pk=pk)
    form = FriendResponseForm(request.POST)
    return form_action_response(request, form, lambda f: respond(friendship, request.user, f.accept))


@login_required
@require_POST
@rate_limit('friend_action', limit=30, fallback='social:friends')
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
