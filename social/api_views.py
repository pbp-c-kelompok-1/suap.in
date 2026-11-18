"""WEB SERVICE (API) modul Social dengan Django REST Framework, untuk aplikasi mobile Flutter.

Bedanya dengan views.py:
    - views.py     -> membalas HTML (dipakai browser / situs web).
    - api_views.py -> membalas JSON (dipakai aplikasi Flutter).
Logika perhitungannya SAMA: semua memanggil services.py dan friends.py, jadi data di
aplikasi mobile selalu sama dengan data di situs web.

Daftar endpoint (awalan /social/api/):
    GET  leaderboard/?tab=national|campus|friends -> peringkat CO2 sepanjang waktu
    GET  campus-war/                              -> peringkat kampus bulan ini
    GET  universities/                            -> daftar kampus (pilihan kampus)
    POST campus/                {university: id}  -> pilih / ganti kampus            (login)
    GET  friends/?q=                              -> teman, permintaan, pencarian    (login)
    POST friends/request/       {username}        -> kirim permintaan teman          (login)
    POST friends/<id>/respond/  {action}          -> terima / tolak                  (login)
    POST friends/<id>/delete/                     -> unfriend / batalkan permintaan  (login)

Pola tiap view (function-based, sama dengan scanner/api_views.py):
    @api_view([...])            -> fungsi biasa menjadi view DRF; method lain ditolak 405
    @authentication_classes     -> cara mengenali user (session cookie)
    @permission_classes         -> AllowAny (boleh tamu) atau IsAuthenticated (wajib login -> 403)
    Response(data, status=...)  -> DRF mengubah dict menjadi JSON
"""
from django.contrib.auth.models import User
from django.db.models import F, Q
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .friends import FriendshipError, friend_ids, relation_status, remove, respond, send_request
from .models import CampusMembership, Friendship, University
from .ratelimit import rate_limit
from .serializers import (
    CampusChoiceSerializer, CampusRankSerializer, FriendRequestSerializer, FriendResponseSerializer,
    FriendRowSerializer, LeaderboardRowSerializer, PendingRequestSerializer, SearchResultSerializer,
    UniversitySerializer, first_error,
)
from .services import carbon_leaderboard, leaderboard_rows, min_scans, month_start, ranked_campuses
from .views import LEADERBOARD_TABS, SEARCH_LIMIT


class MobileSessionAuthentication(SessionAuthentication):
    """Login lewat session cookie (sama dengan situs web), TANPA cek token CSRF.

    Aplikasi Flutter (pbp_django_auth / CookieRequest) mengirim cookie `sessionid` setelah login,
    tetapi tidak mengirim token CSRF seperti form HTML. SessionAuthentication bawaan DRF akan
    menolak POST seperti itu (403 "CSRF Failed"), jadi pengecekan CSRF dimatikan HANYA untuk
    endpoint API ini. Situs web (views.py) tetap memakai CSRF seperti biasa.

    Kenapa tetap aman: cookie session Django memakai SameSite=Lax, sehingga browser tidak
    mengirim cookie itu dalam POST yang datang dari situs lain (inti serangan CSRF).
    """

    def enforce_csrf(self, request):
        return  # sengaja tidak melakukan apa-apa


# Dipakai di semua endpoint supaya cara login-nya seragam.
AUTH = [MobileSessionAuthentication]


def ok(message, http_status=status.HTTP_200_OK, **extra):
    """Bentuk balasan sukses yang seragam: {"ok": true, "message": "...", ...}."""
    return Response({'ok': True, 'message': message, **extra}, status=http_status)


def fail(message, http_status=status.HTTP_400_BAD_REQUEST):
    """Bentuk balasan gagal yang seragam: {"ok": false, "message": "..."} + status 400."""
    return Response({'ok': False, 'message': message}, status=http_status)


# ---------- Leaderboard & Campus War ----------

@api_view(['GET'])
@authentication_classes(AUTH)
@permission_classes([AllowAny])   # tamu boleh melihat tab Nasional
def api_leaderboard(request):
    """Leaderboard CO2 sepanjang waktu. Sama dengan views.leaderboard_view, tapi JSON.

    Contoh: GET /social/api/leaderboard/?tab=campus
    reason: '' | 'login' (tab teman/kampus butuh login) | 'campus' (belum pilih kampus)
            | 'no_friends' (belum punya teman). Aplikasi menampilkan pesan sesuai reason.
    """
    # request.query_params = versi DRF dari request.GET (parameter di URL).
    tab = request.query_params.get('tab', 'national')
    if tab not in dict(LEADERBOARD_TABS):
        tab = 'national'   # nilai aneh -> kembali ke tab Nasional
    ranked, mine, reason = carbon_leaderboard(request.user, tab)
    need = min_scans()
    rows = leaderboard_rows(ranked, request.user)
    return Response({
        'tab': tab,
        'tabs': [{'key': key, 'label': label} for key, label in LEADERBOARD_TABS],
        'min_scans': need,
        'my_scans': mine['scans'] if mine else 0,
        'scans_needed': max(0, need - mine['scans']) if mine else need,
        'reason': reason,
        # many=True -> serializer untuk LIST (setiap elemen diubah jadi dict).
        'results': LeaderboardRowSerializer(rows, many=True).data,
    })


@api_view(['GET'])
@authentication_classes(AUTH)
@permission_classes([AllowAny])
def api_campus_war(request):
    """Campus War bulan ini: rata-rata gram CO2 per scan per kampus."""
    my_campus = None
    if request.user.is_authenticated:
        membership = CampusMembership.objects.filter(user=request.user).select_related('university').first()
        if membership:
            my_campus = UniversitySerializer(membership.university).data
    since = month_start()
    return Response({
        'period_start': since.isoformat(),     # tanggal 1 bulan ini, contoh "2026-11-01"
        'min_scans': min_scans(),
        'my_campus': my_campus,                # null kalau tamu / belum pilih kampus
        'results': CampusRankSerializer(ranked_campuses(since), many=True).data,
    })


@api_view(['GET'])
@authentication_classes(AUTH)
@permission_classes([AllowAny])
def api_universities(request):
    """Daftar semua kampus, untuk pilihan (dropdown) kampus di aplikasi."""
    return Response(UniversitySerializer(University.objects.all(), many=True).data)


@rate_limit('campus', limit=10)   # maks 10 POST per menit; kelebihan -> 429
@api_view(['POST'])
@authentication_classes(AUTH)
@permission_classes([IsAuthenticated])
def api_choose_campus(request):
    """Create/Update CampusMembership. Body JSON: {"university": 1}."""
    instance = CampusMembership.objects.filter(user=request.user).first()
    # instance=None -> serializer.save() membuat baris baru; instance ada -> mengubah baris itu.
    serializer = CampusChoiceSerializer(instance, data=request.data)
    if not serializer.is_valid():
        return fail(first_error(serializer))
    # save(user=...) -> isi kolom user dari user yang login (bukan dari input aplikasi).
    membership = serializer.save(user=request.user)
    return ok(f'Kampusmu sekarang {membership.university.short_name}.',
              campus=UniversitySerializer(membership.university).data)


# ---------- Teman ----------

@api_view(['GET'])
@authentication_classes(AUTH)
@permission_classes([IsAuthenticated])
def api_friends(request):
    """Read: teman, permintaan masuk/keluar, dan hasil pencarian. Sama dengan views.friends_view."""
    me = request.user
    q = request.query_params.get('q', '').strip()[:50]

    # 1. Pencarian username (maks SEARCH_LIMIT hasil, diri sendiri tidak ikut).
    results = []
    if q:
        for u in (User.objects.filter(username__icontains=q).exclude(pk=me.pk)
                  .select_related('campus__university').order_by('username')[:SEARCH_LIMIT]):
            relation, friendship = relation_status(me, u)
            results.append({'user': u, 'status': relation, 'friendship': friendship})

    # 2. Teman, urut XP terbanyak. Coalesce -> user tanpa profil game dapat XP 0.
    friends = (User.objects.filter(pk__in=friend_ids(me))
               .select_related('campus__university')
               .annotate(xp=Coalesce(F('game_profile__total_xp'), 0))
               .order_by('-xp', 'username'))
    friendships = {f.other(me).pk: f for f in Friendship.objects.filter(
        Q(from_user=me) | Q(to_user=me), status=Friendship.ACCEPTED)}
    friend_rows = [{'user': u, 'xp': u.xp, 'friendship': friendships.get(u.pk)} for u in friends]

    # 3. Permintaan yang menunggu. select_related -> data user ikut diambil (mencegah N+1 query).
    incoming = Friendship.objects.filter(to_user=me, status=Friendship.PENDING).select_related(
        'from_user__campus__university', 'to_user')
    outgoing = Friendship.objects.filter(from_user=me, status=Friendship.PENDING).select_related(
        'to_user__campus__university', 'from_user')
    context = {'me': me}   # dibutuhkan PendingRequestSerializer untuk tahu "orang satunya"
    return Response({
        'q': q,
        'results': SearchResultSerializer(results, many=True).data,
        'friends': FriendRowSerializer(friend_rows, many=True).data,
        'incoming': PendingRequestSerializer(incoming, many=True, context=context).data,
        'outgoing': PendingRequestSerializer(outgoing, many=True, context=context).data,
    })


def run_action(action):
    """Jalankan aksi dari friends.py; pesan sukses -> 200, FriendshipError -> 400."""
    try:
        return ok(action())
    except FriendshipError as exc:
        return fail(str(exc))


@rate_limit('friend_request', limit=10)
@api_view(['POST'])
@authentication_classes(AUTH)
@permission_classes([IsAuthenticated])
def api_friend_request(request):
    """Create: kirim permintaan teman. Body JSON: {"username": "budi"}."""
    serializer = FriendRequestSerializer(data=request.data, context={'sender': request.user})
    if not serializer.is_valid():
        return fail(first_error(serializer))
    # Aturan pertemanan (auto-accept, kirim ulang setelah ditolak, dst.) tetap di friends.send_request.
    return run_action(lambda: send_request(request.user, serializer.receiver))


@rate_limit('friend_action', limit=30)
@api_view(['POST'])
@authentication_classes(AUTH)
@permission_classes([IsAuthenticated])
def api_friend_respond(request, pk):
    """Update: terima / tolak permintaan. Body JSON: {"action": "accept"} atau {"action": "reject"}."""
    friendship = get_object_or_404(Friendship, pk=pk)   # id tidak ada -> 404 JSON
    serializer = FriendResponseSerializer(data=request.data)
    if not serializer.is_valid():
        return fail(first_error(serializer))
    accept = serializer.validated_data['action'] == 'accept'
    # Cek "hanya penerima yang boleh menjawab" ada di friends.respond.
    return run_action(lambda: respond(friendship, request.user, accept))


@rate_limit('friend_action', limit=30)
@api_view(['POST'])
@authentication_classes(AUTH)
@permission_classes([IsAuthenticated])
def api_friend_delete(request, pk):
    """Delete: unfriend / batalkan permintaan yang dikirim. Cek kepemilikan ada di friends.remove."""
    friendship = get_object_or_404(Friendship, pk=pk)
    return run_action(lambda: remove(friendship, request.user))
