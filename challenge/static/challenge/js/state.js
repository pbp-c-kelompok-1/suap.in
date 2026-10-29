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

/* Kirim POST JSON ke server (dengan CSRF). Mengembalikan { ok, status, data }. */
export async function post(url, body = {}) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': urls.csrf || '' },
    credentials: 'same-origin',
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  return { ok: res.ok && data.ok !== false, status: res.status, data };
}

export const state = {
  user: d.user || { id: 0, name: '' },
  xp: g.xp || 0, cap: g.cap || 0, level: g.level || 1, tier: g.tier || 'Pemula Sadar',
  streak: g.streak || 0, freeze: g.freezes || 0,
  budget: { used: (d.budget || {}).usedKg || 0, max: (d.budget || {}).maxKg || 2 },
  scansToday: d.scansToday || 0,
  totalScans: d.totalScans || 0,
  userTotalCarbon: d.userTotalCarbon || 0,
  quests: d.quests || [],
  chest: d.chest || { ready: false, claimed: false },
  weekly: d.weekly || [],
  hasWeekData: !!d.hasWeekData,
  weeklyRanking: d.weeklyRanking || null,
  rank,
  notifs: (d.notifs || []).map(n => ({ ...n })),
  stats: d.stats || { scans: 0, recordStreak: 0, avoidedKg: 0, campusRank: null },
  badges: d.badges || [],
  filter: 'all',
  rankTab: rank.kampus.empty === 'no_campus' ? 'nasional' : 'kampus',
  avatar: (d.user || {}).avatar || 0, pending: (d.user || {}).avatar || 0, pTab: 'all', demoUnlock: false,
  profile: { name: (d.user || {}).name || '', bio: (d.user || {}).bio || '' },
};
export const fmt = n => n.toLocaleString('id-ID', { minimumFractionDigits: 1, maximumFractionDigits: 1 });


