from datetime import datetime, time, timedelta

from django.contrib.auth.models import User
from django.db.models import Avg, Count, F, Q, Sum
from django.db.models.functions import Coalesce
from django.templatetags.static import static
from django.utils import timezone
from django.utils.timesince import timesince

from scanner.services import get_carbon_status

from .models import Canteen, CommunityPost, University

# ---------- XP & Leaderboard ----------
# Sumber XP: modul gamification.
#   - Total sepanjang waktu  -> GameProfile.total_xp      (leaderboard Peringkat, modul social)
#   - XP dalam suatu periode -> jumlah XPActivity periode itu (leaderboard mingguan di Laporan
#                               modul challenge, dan Campus War bulanan)


def week_start():
    today = timezone.localdate()
    return today - timedelta(days=today.weekday())


def month_start():
    return timezone.localdate().replace(day=1)


def start_of(day):
    """Tanggal -> datetime jam 00:00 waktu lokal (untuk filter created_at)."""
    return timezone.make_aware(datetime.combine(day, time.min))


def users_with_xp(since=None):
    """User yang punya XP, urut terbesar. since=None: total sepanjang waktu; since=tanggal: XP sejak tanggal itu."""
    if since is None:
        xp = Coalesce(F('game_profile__total_xp'), 0)
    else:
        xp = Coalesce(Sum('xp_activities__amount', filter=Q(xp_activities__created_at__gte=start_of(since))), 0)
    return (
        User.objects.annotate(xp=xp)
        .filter(xp__gt=0)
        .select_related('campus__university')
        .order_by('-xp', 'username')
    )


def scope_ranking(users, viewer, scope):
    """Batasi ranking ke 'friends' / 'campus' / 'national'.

    Return (queryset, alasan_kosong) dengan alasan '' | 'login' | 'campus' | 'no_friends'.
    """
    from .friends import friend_ids

    if scope == 'national':
        return users, ''
    if not viewer.is_authenticated:
        return users.none(), 'login'
    if scope == 'campus':
        membership = getattr(viewer, 'campus', None)
        if membership is None:
            return users.none(), 'campus'
        return users.filter(campus__university=membership.university), ''
    ids = friend_ids(viewer)
    return users.filter(pk__in=ids | {viewer.pk}), ('' if ids else 'no_friends')


def ranked_campuses(since):
    """Campus War: XP yang dikumpulkan anggota tiap kampus sejak `since`, dirata-rata per anggota."""
    gained = Coalesce(
        Sum('members__user__xp_activities__amount',
            filter=Q(members__user__xp_activities__created_at__gte=start_of(since))),
        0,
    )
    campuses = list(University.objects.annotate(member_count=Count('members', distinct=True), total_xp=gained))
    for c in campuses:
        c.avg_xp = round(c.total_xp / c.member_count, 1) if c.member_count else 0
    campuses.sort(key=lambda c: (-c.avg_xp, c.short_name))
    return campuses


# ---------- Community ----------

RANGE_DAYS = {'today': 0, 'week': 6}


def community_posts_since(range_key):
    """Post publik (dibagikan & tidak disembunyikan) dalam rentang waktu tertentu."""
    posts = CommunityPost.objects.filter(is_shared=True, is_hidden=False)
    if range_key in RANGE_DAYS:
        since = timezone.localdate() - timedelta(days=RANGE_DAYS[range_key])
        posts = posts.filter(created_at__date__gte=since)
    return posts


def canteen_pins(range_key='today', faculty=''):
    """Data pin peta: tiap kantin aktif + jumlah post + rata-rata CO2 per post."""
    posts = community_posts_since(range_key)
    canteens = Canteen.objects.filter(is_active=True)
    if faculty:
        canteens = canteens.filter(faculty=faculty)

    stats = {
        row['canteen']: row
        for row in posts.filter(canteen__in=canteens)
        .values('canteen')
        .annotate(post_count=Count('id'), avg_co2=Avg('total_co2_grams'))
    }

    pins = []
    for c in canteens:
        row = stats.get(c.id, {})
        count = row.get('post_count', 0)
        avg = round(row['avg_co2']) if count else None
        pins.append({
            'id': c.id,
            'name': c.name,
            'faculty': c.faculty,
            'lat': float(c.latitude),
            'lng': float(c.longitude),
            'post_count': count,
            'avg_co2': avg,
            'status': get_carbon_status(avg)[0] if count else 'none',
        })
    return pins


POSTS_PER_PAGE = 20


def time_ago(dt):
    """'2 jam lalu' — waktu dibuat kasar sesuai PRD (tanpa jam persis)."""
    delta = timezone.now() - dt
    if delta.total_seconds() < 60:
        return 'baru saja'
    return timesince(dt).split(',')[0] + ' lalu'


def canteen_posts(canteen, range_key='today', page=1):
    """Ringkasan + satu halaman foto untuk panel kantin."""
    posts = community_posts_since(range_key).filter(canteen=canteen).select_related('user')
    summary = posts.aggregate(post_count=Count('id'), avg_co2=Avg('total_co2_grams'), avg_price=Avg('price'))

    start = (page - 1) * POSTS_PER_PAGE
    chunk = list(posts[start:start + POSTS_PER_PAGE + 1])
    has_more = len(chunk) > POSTS_PER_PAGE

    return {
        'canteen': {'id': canteen.id, 'name': canteen.name, 'faculty': canteen.faculty},
        'summary': {
            'post_count': summary['post_count'],
            'avg_co2': round(summary['avg_co2']) if summary['avg_co2'] is not None else None,
            'avg_price': round(summary['avg_price']) if summary['avg_price'] is not None else None,
        },
        'posts': [
            {
                'id': p.id,
                'photo_url': static(p.seed_image) if p.seed_image else (p.photo.url if p.photo else ''),
                'food_name': p.food_name,
                'price': p.price,
                'co2': round(p.total_co2_grams),
                'status': get_carbon_status(p.total_co2_grams)[0],
                'username': p.user.username,
                'time_ago': time_ago(p.created_at),
            }
            for p in chunk[:POSTS_PER_PAGE]
        ],
        'page': page,
        'has_more': has_more,
    }
