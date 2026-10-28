// State aplikasi (data dummy) + tier & formatter

const real = window.SUAPIN_REAL || null;
const realWeekly = real ? real.weekly.map(w => ({ d: w.d, v: w.v, hasData: w.hasData })) : null;
// rank dari server: { teman: [...], kampus: [...], nasional: [...] } berisi XP minggu ini
const realRank = real ? Object.fromEntries(
  Object.entries(real.rank).map(([tab, rows]) => [tab, rows.map(r => [r.name, r.xp, r.is_me ? 1 : 0])])
) : null;

/* ---------------- STATE ---------------- */
export const state = {
  xp: 340, cap: 500, level: 12, streak: 7,
  budget: { used: 2.1, max: 3.5 },
  budgetCapKg: real ? real.budgetCapKg : 3.5,
  freeze: 1,
  quests: [
    { id: 1, icon: 'leaf',   tone: 'green', title: 'Menu nabati siang ini', desc: 'Ganti 1 porsi lauk hewani dengan tempe, tahu, atau sayur.', goal: 1, val: 0, xp: 30, why: 'Karena kamu sering makan daging sapi', claimed: false },
    { id: 2, icon: 'camera', tone: 'blue',  title: 'Foto 3 makanan', desc: 'Scan sarapan, makan siang, dan makan malam.',            goal: 3, val: 2, xp: 20, why: 'Kamu biasanya lupa foto makan malam', claimed: false },
    { id: 3, icon: 'plate',  tone: 'teal',  title: 'Habiskan piringmu', desc: 'Habiskan 2 porsi tanpa sisa.',                          goal: 2, val: 0, xp: 25, why: 'Sisa makanan menambah emisi ± 0,4 kg', claimed: false },
  ],
  chestOpen: false,
  weekly: realWeekly || [
    { d: 'Sen', v: 2.4 }, { d: 'Sel', v: 3.1 }, { d: 'Rab', v: 2.2 }, { d: 'Kam', v: 3.6 },
    { d: 'Jum', v: 2.9 }, { d: 'Sab', v: 2.5 }, { d: 'Min', v: 1.7 },
  ],
  rank: {
    teman:    realRank ? realRank.teman : [['Dinda', 240], ['Kamu', 180, 1], ['Bima', 150], ['Salsa', 90]],
    kampus:   realRank ? realRank.kampus : [['Dinda A.', 260], ['Bima R.', 210], ['Kamu', 180, 1], ['Salsa P.', 120], ['Raka T.', 60]],
    nasional: realRank ? realRank.nasional : [['Alya N.', 420], ['Fajar S.', 390], ['Citra W.', 310], ['Kamu', 180, 1], ['Gilang M.', 150]],
  },
  notifs: [
    { id: 1, type: 'streak',    ico: 'flame',  tone: 'amber', t: 'Streak 7 hari!', p: 'Sedikit lagi ke lencana "Streak 14 Hari".', time: '5 mnt', read: false },
    { id: 2, type: 'misi',      ico: 'target', tone: 'green', t: '3 misi baru menunggumu', p: 'Dibuat dari kebiasaan makanmu minggu ini.', time: '1 jam', read: false },
    { id: 3, type: 'peringkat', ico: 'trophy', tone: 'blue',  t: 'Kamu naik ke peringkat 3 kampus', p: 'Bima R. dilewati. Pertahankan!', time: '3 jam', read: false },
    { id: 4, type: 'streak',    ico: 'flame',  tone: 'red',   t: 'Streakmu terancam hilang', p: 'Belum ada foto makanan hari ini. Foto sebelum 23.59.', time: 'Kemarin', read: true },
    { id: 5, type: 'misi',      ico: 'check',  tone: 'teal',  t: 'Misi "Foto 3 makanan" selesai', p: 'Kamu dapat +20 XP.', time: 'Kemarin', read: true },
    { id: 6, type: 'peringkat', ico: 'trophy', tone: 'blue',  t: 'Dinda menantangmu 1v1', p: 'Adu emisi terendah selama 3 hari.', time: '2 hari', read: true },
  ],
  filter: 'all', rankTab: 'kampus',
  avatar: 0, pending: 0, pTab: 'all', demoUnlock: false,
  profile: { name: real ? real.profileName : 'Kamu', bio: 'Lagi belajar makan lebih hijau.' },
};
const tiers = [[0, 'Pemula Sadar'], [10, 'Pejuang Hijau'], [20, 'Guardian Bumi'], [35, 'Legenda Lestari']];
export const tierFor = l => [...tiers].reverse().find(t => l >= t[0])[1];
export const fmt = n => n.toLocaleString('id-ID', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
