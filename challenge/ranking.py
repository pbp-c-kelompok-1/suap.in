"""Peringkat mingguan Challenge.

Aturan:
- Satu minggu = Senin sampai Minggu (zona waktu lokal).
- Hanya pengguna yang punya minimal MIN_SCANS_FOR_RANK scan dalam minggu itu
  yang masuk peringkat. Pengguna tanpa scan TIDAK PERNAH masuk daftar.
- Urutan: rata-rata gram CO2 per scan, paling kecil = peringkat teratas.
  Dipilih rata-rata (bukan total) supaya yang rajin scan semua makanannya
  tidak kalah dari yang hanya scan sekali-dua kali.
  Seri: scan lebih banyak menang, lalu urut username.
- Riwayat dihitung langsung dari FoodLog untuk HISTORY_WEEKS minggu terakhir.
  Tidak ada tabel snapshot, jadi riwayat tidak bisa tidak sinkron dengan data scan.
"""
import math
from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncWeek
from django.utils import timezone

from scanner.models import FoodLog
from social.models import CampusMembership

from .models import ChallengeProfile

MIN_SCANS_FOR_RANK = 3
HISTORY_WEEKS = 16  # sekitar 4 bulan
TOP_N = 10

# Teks bisa diubah di sini saja.
LIVE_NOTICE = (
    'Kamu masih bertanding! Rekap akan terdata setelah pertandingan minggu ini '
    'selesai. Semangat meraih juara 1-nya!'
)


def week_start(day):
    return day - timedelta(days=day.weekday())


def friend_user_ids(user):
    """SATU-SATUNYA tempat yang menentukan siapa "teman" seorang user di peringkat.

    Teman = pertemanan yang sudah DITERIMA di modul social (menu Teman), ditambah
    pengguna yang pernah saling tantang lewat FriendChallenge (active atau finished). Tab Teman di Laporan
    dan di halaman Peringkat (social) sama-sama memanggil fungsi ini.
    """
    from social.friends import friend_ids
    from story.models import FriendChallenge

    accepted = FriendChallenge.objects.filter(status__in=('active', 'finished'))
    sent = accepted.filter(challenger=user).values_list('opponent_id', flat=True)
    received = accepted.filter(opponent=user).values_list('challenger_id', flat=True)
    return set(friend_ids(user)) | set(sent) | set(received)


def _weekly_entries(first_monday, last_day):
    """{senin: [entry]} -- satu entry per (pengguna, minggu) yang punya scan."""
    rows = (
        FoodLog.objects
        .filter(scanned_at__date__gte=first_monday, scanned_at__date__lte=last_day)
        .annotate(week=TruncWeek('scanned_at'))
        .order_by()
        .values('user_id', 'user__username', 'week')
        .annotate(
            # satu foto = satu scan (semua item satu foto punya respons AI yang sama)
            scans=(
                Count('ai_raw_response', filter=~Q(ai_raw_response=''), distinct=True)
                + Count('id', filter=Q(ai_raw_response=''))
            ),
            co2=Sum('co2_grams'),
        )
    )
    by_week = {}
    for r in rows:
        wk = r['week']
        monday = timezone.localtime(wk).date() if timezone.is_aware(wk) else wk.date()
        carbon = r['co2'] or 0
        by_week.setdefault(monday, []).append({
            'user_id': r['user_id'],
            'username': r['user__username'],
            'scans': r['scans'],
            'carbon': carbon,
            'avg': carbon / r['scans'],
        })
    return by_week


def rank_entries(entries, min_scans=MIN_SCANS_FOR_RANK):
    """Urutkan yang memenuhi syarat dan beri nomor 'pos'."""
    eligible = [e for e in entries if e['scans'] >= min_scans]
    eligible.sort(key=lambda e: (e['avg'], -e['scans'], e['username']))
    return [dict(e, pos=i) for i, e in enumerate(eligible, start=1)]


def weekly_positions(user, first_monday, last_day):
    """{senin: {'pos','total','campus_pos','campus_total'}} untuk minggu-minggu yang dimaksud.

    Dipakai Laporan supaya peringkat tiap minggu memakai aturan yang sama persis
    dengan leaderboard (rata-rata emisi per scan, minimal MIN_SCANS_FOR_RANK).
    """
    by_week = _weekly_entries(first_monday, last_day)
    membership = CampusMembership.objects.filter(user=user).select_related('university').first()
    campus_ids = set()
    if membership:
        campus_ids = set(
            CampusMembership.objects.filter(university=membership.university)
            .values_list('user_id', flat=True)
        )
    out = {}
    for monday, entries in by_week.items():
        nat = _find(rank_entries(entries), user.pk)
        camp_ranked = rank_entries([e for e in entries if e['user_id'] in campus_ids]) if membership else []
        camp = _find(camp_ranked, user.pk)
        out[monday] = {
            'pos': nat['pos'] if nat else None,
            'total': len(rank_entries(entries)),
            'campus_pos': camp['pos'] if camp else None,
            'campus_total': len(camp_ranked),
        }
    return out


def _find(ranked, user_id):
    return next((e for e in ranked if e['user_id'] == user_id), None)


def _profiles(user_ids):
    return {
        p.user_id: p
        for p in ChallengeProfile.objects.filter(user_id__in=list(user_ids))
    }


def _item(entry, user, profiles):
    p = profiles.get(entry['user_id'])
    return {
        'pos': entry['pos'],
        'name': (p.display_name if p and p.display_name else entry['username']),
        'avatar': p.avatar_id if p else 0,
        'scans': entry['scans'],
        'carbon': round(entry['carbon']),
        'kg': round(entry['carbon'] / 1000, 2),
        'avg': round(entry['avg']),
        'is_me': user is not None and entry['user_id'] == user.pk,
    }


def _items(ranked, user, profiles):
    shown = ranked[:TOP_N]
    me = _find(ranked, user.pk)
    if me is not None and me not in shown:
        shown = shown + [me]
    return [_item(e, user, profiles) for e in shown]


def _empty_code(my_entry, ever_scanned):
    if not ever_scanned:
        return 'no_scan'
    if my_entry is None:
        return 'no_scan_week'
    if my_entry['scans'] < MIN_SCANS_FOR_RANK:
        return 'few_scans'
    return ''


def _message(pos, total, delta, my_entry, ever_scanned):
    """(tone, teks) untuk kartu rekap."""
    code = _empty_code(my_entry, ever_scanned)
    if code == 'no_scan':
        return 'start', 'Kamu belum pernah scan. Yuk mulai scan makananmu!'
    if code == 'no_scan_week':
        return 'start', 'Belum ada aktivitas minggu ini. Yuk mulai scan makananmu!'
    if code == 'few_scans':
        need = MIN_SCANS_FOR_RANK - my_entry['scans']
        return 'start', f'Scan {need} makanan lagi minggu ini supaya kamu masuk peringkat.'

    if pos == 1:
        text, tone = 'Kamu peringkat 1 minggu ini! Pertahankan pilihan makanan rendah karbonmu.', 'top'
    elif pos <= 3:
        text, tone = 'Keren, kamu masuk 3 besar! Sedikit lagi ke puncak, pertahankan ya.', 'top'
    elif pos <= math.ceil(total / 2):
        text, tone = 'Kamu ada di paruh atas. Terus pertahankan, yuk!', 'good'
    else:
        text, tone = ('Belum di atas, tapi masih ada waktu untuk naik. '
                      'Coba ganti satu menu berdaging dengan menu nabati. Semangat!'), 'push'

    if delta:
        if delta > 0:
            text += f' Naik {delta} peringkat dari minggu lalu.'
        else:
            text += f' Turun {abs(delta)} peringkat dari minggu lalu, ayo kejar lagi.'
    return tone, text


def compute_leaderboard(user, today=None):
    today = today or timezone.localdate()
    cur_monday = week_start(today)
    first_monday = cur_monday - timedelta(weeks=HISTORY_WEEKS - 1)
    by_week = _weekly_entries(first_monday, today)

    membership = (
        CampusMembership.objects.filter(user=user).select_related('university').first()
    )
    campus_ids = set()
    if membership:
        campus_ids = set(
            CampusMembership.objects
            .filter(university=membership.university)
            .values_list('user_id', flat=True)
        )

    friend_ids = set(friend_user_ids(user)) - {user.pk}

    ever_scanned = FoodLog.objects.filter(user=user).exists()
    total_carbon = (
        FoodLog.objects.filter(user=user).aggregate(t=Sum('co2_grams'))['t'] or 0
    )

    weeks = {}
    mondays = [first_monday + timedelta(weeks=i) for i in range(HISTORY_WEEKS)]
    for monday in mondays:
        entries = by_week.get(monday, [])
        nat = rank_entries(entries)
        camp = rank_entries([e for e in entries if e['user_id'] in campus_ids]) if membership else []
        circle = friend_ids | {user.pk}
        frnd = rank_entries([e for e in entries if e['user_id'] in circle]) if friend_ids else []
        weeks[monday] = {
            'mine': _find(entries, user.pk),
            'nat': nat,
            'camp': camp,
            'frnd': frnd,
        }

    cur = weeks[cur_monday]
    prev = weeks[cur_monday - timedelta(weeks=1)]

    nat_me = _find(cur['nat'], user.pk)
    camp_me = _find(cur['camp'], user.pk)
    prev_me = _find(prev['nat'], user.pk)
    delta = (prev_me['pos'] - nat_me['pos']) if (prev_me and nat_me) else 0

    shown_ids = {e['user_id'] for e in cur['nat'][:TOP_N] + cur['camp'][:TOP_N] + cur['frnd'][:TOP_N]}
    shown_ids.add(user.pk)
    profiles = _profiles(shown_ids)

    def scope(ranked, first_empty=''):
        code = first_empty or _empty_code(cur['mine'], ever_scanned)
        me = _find(ranked, user.pk)
        return {
            'items': [] if code else _items(ranked, user, profiles),
            'empty': code,
            'position': me['pos'] if me else None,
            'total': len(ranked),
            'need': (MIN_SCANS_FOR_RANK - cur['mine']['scans']) if code == 'few_scans' else 0,
        }

    rank = {
        'teman': scope(cur['frnd'], '' if friend_ids else 'no_friends'),
        'kampus': scope(cur['camp'], '' if membership else 'no_campus'),
        'nasional': scope(cur['nat']),
    }

    # ---- riwayat: minggu yang sudah selesai, mulai dari minggu scan pertama ----
    first_active = next((m for m in mondays if weeks[m]['mine']), None)
    history = []
    if first_active:
        for monday in reversed(mondays[:-1]):
            if monday < first_active:
                break
            w = weeks[monday]
            mine = w['mine']
            nat_pos = _find(w['nat'], user.pk)
            camp_pos = _find(w['camp'], user.pk)
            if mine is None:
                status = 'none'
            elif mine['scans'] < MIN_SCANS_FOR_RANK:
                status = 'few'
            else:
                status = 'ranked'
            history.append({
                'weekStart': monday.isoformat(),
                'weekEnd': (monday + timedelta(days=6)).isoformat(),
                'status': status,
                'position': nat_pos['pos'] if nat_pos else None,
                'total': len(w['nat']),
                'campusPosition': camp_pos['pos'] if camp_pos else None,
                'campusTotal': len(w['camp']),
                'scans': mine['scans'] if mine else 0,
                'avg': round(mine['avg']) if mine else 0,
            })

    tone, message = _message(
        nat_me['pos'] if nat_me else None, len(cur['nat']), delta,
        cur['mine'], ever_scanned,
    )
    top = [_item(e, user, profiles) for e in cur['nat'][:3]] if nat_me else []

    live_notice = None
    if nat_me:
        days_left = (cur_monday + timedelta(days=6) - today).days
        live_notice = LIVE_NOTICE + (
            f' Sisa {days_left} hari lagi.' if days_left > 0 else ' Hari ini hari terakhir!'
        )

    recap = {
        'weekStart': cur_monday.isoformat(),
        'weekEnd': (cur_monday + timedelta(days=6)).isoformat(),
        'position': nat_me['pos'] if nat_me else None,
        'totalUsers': len(cur['nat']),
        'campusPosition': camp_me['pos'] if camp_me else None,
        'campusTotal': len(cur['camp']),
        'hasCampus': bool(membership),
        'scans': cur['mine']['scans'] if cur['mine'] else 0,
        'avg': round(cur['mine']['avg']) if cur['mine'] else 0,
        'minScans': MIN_SCANS_FOR_RANK,
        'delta': delta,
        'tone': tone,
        'message': message,
        'liveNotice': live_notice,
        'top': top,
        'history': history,
        'historyWeeks': HISTORY_WEEKS,
    }
    return {
        'rank': rank,
        'recap': recap,
        'userTotalCarbon': total_carbon,
        'campusRank': camp_me['pos'] if camp_me else None,
    }


def leaderboard_for(user, scope, today=None, limit=50):
    """Daftar peringkat minggu ini untuk halaman Leaderboard sosial.

    Memakai aturan dan data yang SAMA dengan peringkat di Laporan, jadi posisi
    seseorang tidak pernah beda antara dua halaman. `user` boleh anonim (hanya
    scope 'nasional'). Mengembalikan (items, kode_kosong).
    """
    today = today or timezone.localdate()
    monday = week_start(today)
    entries = _weekly_entries(monday, today).get(monday, [])
    authed = bool(user and user.is_authenticated)

    if scope == 'kampus':
        if not authed:
            return [], 'need_login'
        membership = CampusMembership.objects.filter(user=user).first()
        if not membership:
            return [], 'no_campus'
        ids = set(CampusMembership.objects.filter(university=membership.university)
                  .values_list('user_id', flat=True))
        entries = [e for e in entries if e['user_id'] in ids]
    elif scope == 'teman':
        if not authed:
            return [], 'need_login'
        friends = friend_user_ids(user)
        if not friends:
            return [], 'no_friends'
        entries = [e for e in entries if e['user_id'] in (friends | {user.pk})]

    ranked = rank_entries(entries)[:limit]
    profiles = _profiles([e['user_id'] for e in ranked])
    campuses = {
        m.user_id: m.university.short_name
        for m in CampusMembership.objects.filter(user_id__in=[e['user_id'] for e in ranked])
        .select_related('university')
    }
    items = []
    for e in ranked:
        item = _item(e, user if authed else None, profiles)
        item['is_me'] = authed and e['user_id'] == user.pk
        item['campus'] = campuses.get(e['user_id'], '')
        items.append(item)
    return items, ''


def build_rankings(user, today=None):
    data = compute_leaderboard(user, today)
    return {
        'rank': data['rank'],
        'userTotalCarbon': data['userTotalCarbon'],
        'campusRank': data['campusRank'],
    }


def build_weekly_ranking_recap(user, today=None):
    return compute_leaderboard(user, today)['recap']
