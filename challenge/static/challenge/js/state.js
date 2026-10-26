// State halaman Challenge. Semua data datang dari server lewat <script id="suapin-data">
// (json_script) dan tombol/URL lewat #suapin-cfg. Tidak ada data contoh di sini.

const dataEl = document.getElementById('suapin-data');
const cfgEl = document.getElementById('suapin-cfg');
const d = dataEl ? JSON.parse(dataEl.textContent) : {};
const g = d.game || {};
const rank = d.rank || {
  teman: { items: [], empty: 'no_friends' },
  kampus: { items: [], empty: 'no_campus' },
  nasional: { items: [], empty: 'no_data' },
};

export const urls = cfgEl ? { ...cfgEl.dataset } : {};

/* Status baca/hapus notifikasi disimpan per user di browser (belum ada tabel di server). */
const NOTIF_KEY = `suapin-notif-${(d.user || {}).id || 'anon'}`;
function loadLocal() {
  try { return JSON.parse(localStorage.getItem(NOTIF_KEY)) || { read: [], gone: [] }; }
  catch { return { read: [], gone: [] }; }
}
const local = loadLocal();
export function saveNotifLocal() {
  try {
    localStorage.setItem(NOTIF_KEY, JSON.stringify({
      read: state.notifs.filter(n => n.read).map(n => n.id),
      gone: local.gone,
    }));
  } catch { /* storage tidak tersedia: status baca hanya berlaku di sesi ini */ }
}
export function markGone(id) { if (!local.gone.includes(id)) local.gone.push(id); }

export const state = {
  user: d.user || { id: 0, name: '' },
  xp: g.xp || 0, cap: g.cap || 0, level: g.level || 1, tier: g.tier || 'Pemula Sadar',
  streak: g.streak || 0, freeze: g.freezes || 0,
  budget: { used: (d.budget || {}).usedKg || 0, max: (d.budget || {}).maxKg || 2 },
  scansToday: d.scansToday || 0,
  totalScans: d.totalScans || 0,
  quests: d.quests || [],
  chest: d.chest || { ready: false, claimed: false },
  weekly: d.weekly || [],
  hasWeekData: !!d.hasWeekData,
  rank,
  notifs: (d.notifs || []).filter(n => !local.gone.includes(n.id)).map(n => ({ ...n, read: local.read.includes(n.id) })),
  stats: d.stats || { scans: 0, recordStreak: 0, avoidedKg: 0, campusRank: null },
  badges: d.badges || [],
  filter: 'all',
  rankTab: rank.kampus.empty === 'no_campus' ? 'nasional' : 'kampus',
  avatar: 0, pending: 0, pTab: 'all', demoUnlock: false,
  profile: { name: (d.user || {}).name || '', bio: '' },
};
export const fmt = n => n.toLocaleString('id-ID', { minimumFractionDigits: 1, maximumFractionDigits: 1 });


from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone

from scanner.models import FoodLog, CarbonBudget


@login_required
def api_challenge_data(request):
    user = request.user
    today = timezone.localdate()
    week_start = today - timedelta(days=6)

    logs_today = FoodLog.objects.filter(
        user=user,
        scanned_at__date=today,
    )

    weekly_logs = FoodLog.objects.filter(
        user=user,
        scanned_at__date__gte=week_start,
        scanned_at__date__lte=today,
    )

    budget = CarbonBudget.objects.filter(
        user=user,
        date=today,
    ).first()

    daily_grams = sum(log.co2_grams for log in logs_today)
    weekly_grams = sum(log.co2_grams for log in weekly_logs)

    daily_logs = list(logs_today)

    return JsonResponse({
        "user": {
            "id": user.id,
            "name": user.username,
        },
        "scans_today": len(daily_logs),
        "total_scans": FoodLog.objects.filter(user=user).count(),
        "daily_co2_kg": round(daily_grams / 1000, 2),
        "weekly_co2_kg": round(weekly_grams / 1000, 2),
        "daily_budget_kg": round(
            (budget.budget_grams if budget else 2000) / 1000, 2
        ),
        "weekly": [
            {
                "day": (week_start + timedelta(days=i)).strftime("%a"),
                "co2_kg": round(sum(
                    log.co2_grams
                    for log in weekly_logs
                    if timezone.localtime(log.scanned_at).date()
                    == week_start + timedelta(days=i)
                ) / 1000, 2),
            }
            for i in range(7)
        ],
    })

