// Halaman Laporan: grafik mingguan + peringkat. Semua dari data server.
import { $, $$, ico } from './utils.js';
import { avatarIcon } from './avatar.js';
import { fmt, state } from './state.js';
import { toast } from './fx.js';
import { ACT, emptyCard } from './empty.js';

const show = (el, on) => { el.hidden = !on; el.style.display = on ? '' : 'none'; };

export function renderReport() {
  const bars = $('#bars'), empty = $('#barsEmpty'), legend = $('#barsLegend');
  if (!state.hasWeekData) {
    show(bars, false); show(legend, false); show(empty, true);
    empty.innerHTML = emptyCard({
      title: 'Belum ada scan minggu ini',
      text: 'Grafik emisimu muncul setelah kamu scan makanan pertama.',
      actions: [ACT.scan(true), ACT.friends(false)],
      flat: true,
    });
    return;
  }
  show(bars, true); show(legend, true); show(empty, false);
  const cap = state.budget.max;
  const withData = state.weekly.filter(w => w.hasData);
  const best = Math.min(...withData.map(w => w.v));
  const max = Math.max(cap, ...state.weekly.map(w => w.v), 0.1) * 1.2;
  bars.innerHTML =
    `<div class="cap" style="bottom:calc(${cap / max * 100}% * .88 + 28px)"><span>Budget ${fmt(cap).replace('.', ',')}</span></div>` +
    state.weekly.map(w => {
      const cls = !w.hasData ? 'nodata' : w.v > cap ? 'over' : w.v === best ? 'best' : '';
      const label = w.hasData ? `${w.d}: ${fmt(w.v).replace('.', ',')} kg CO₂` : `${w.d}: belum ada data`;
      const tip = w.hasData ? `${fmt(w.v).replace('.', ',')} kg` : 'Belum ada data';
      return `<div class="col" role="listitem"><button class="pillar ${cls}" data-h="${w.hasData ? w.v / max * 100 : 4}" aria-label="${label}"><span class="tip">${tip}</span></button><small>${w.d}</small></div>`;
    }).join('');
}

export function animateReport() {
  const total = state.weekly.reduce((a, b) => a + b.v, 0);
  const el = $('#weekTotal'); const t0 = performance.now();
  (function tick(t) {
    const p = Math.min(1, (t - t0) / 900), e = 1 - Math.pow(1 - p, 3);
    el.textContent = fmt(total * e).replace('.', ',');
    if (p < 1) requestAnimationFrame(tick);
  })(t0);
  $$('.pillar').forEach((b, i) => { b.style.height = '0'; setTimeout(() => { b.style.height = `calc(${b.dataset.h}% * .88)`; }, 80 + i * 70); });
}

// Nama tampilan diisi bebas oleh user, jadi wajib di-escape sebelum masuk innerHTML.
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => (
  { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
));

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'];
const parseDay = s => { const [y, m, d] = s.split('-').map(Number); return { y, m: m - 1, d }; };

// "26-31 Okt 2026", "26 Okt - 1 Nov 2026", atau lintas tahun.
export function formatRange(startIso, endIso) {
  const a = parseDay(startIso), b = parseDay(endIso);
  if (a.y === b.y && a.m === b.m) return `${a.d}\u2013${b.d} ${MONTHS[b.m]} ${b.y}`;
  if (a.y === b.y) return `${a.d} ${MONTHS[a.m]} \u2013 ${b.d} ${MONTHS[b.m]} ${b.y}`;
  return `${a.d} ${MONTHS[a.m]} ${a.y} \u2013 ${b.d} ${MONTHS[b.m]} ${b.y}`;
}

const minScans = () => (state.weeklyRanking && state.weeklyRanking.minScans) || 3;
const num = n => Number(n || 0).toLocaleString('id-ID');

// Alur "belum bisa tampil peringkat": kode ditentukan server (satu sumber kebenaran).
const EMPTY = {
  no_friends: () => ({
    title: 'Kamu belum punya teman',
    text: 'Tambah teman untuk adu emisi tiap minggu.',
    actions: [ACT.friends(true)],
  }),
  no_campus: () => ({
    title: 'Kamu belum memilih kampus',
    text: 'Pilih kampusmu untuk melihat peringkat teman satu kampus.',
    actions: [ACT.campus(true)],
  }),
  no_scan: () => ({
    title: 'Kamu belum pernah scan',
    text: 'Scan makanan dulu untuk melihat posisimu di peringkat.',
    actions: [ACT.scan(true)],
  }),
  no_scan_week: () => ({
    title: 'Belum ada scan minggu ini',
    text: 'Scan makananmu minggu ini supaya kamu masuk peringkat.',
    actions: [ACT.scan(true)],
  }),
  few_scans: tab => ({
    title: `Scan ${tab.need} makanan lagi`,
    text: `Peringkat dihitung dari minimal ${minScans()} scan per minggu. Sedikit lagi kamu masuk!`,
    actions: [ACT.scan(true)],
  }),
  no_data: () => ({
    title: 'Belum ada peringkat',
    text: 'Belum ada yang masuk peringkat minggu ini. Jadilah yang pertama!',
    actions: [ACT.scan(true)],
  }),
};

const rowHtml = r => `
  <li class="${r.is_me ? 'me' : ''}">
    <span class="pos ${r.pos <= 3 ? 'p' + r.pos : ''}">${r.pos}</span>
    <span class="av avme">${avatarIcon(r.is_me ? state.avatar : r.avatar)}</span>
    <span class="nm">${r.is_me ? 'Kamu' : esc(r.name)}<small class="nm-sub">${r.scans} scan \u00b7 total ${fmt(r.kg).replace('.', ',')} kg</small></span>
    <span class="co">${num(r.avg)} <small>g/scan</small></span>
  </li>`;

function historyRow(h, min) {
  const range = formatRange(h.weekStart, h.weekEnd);
  let main, sub;
  if (h.status === 'ranked') {
    main = `<span class="wh-pos ${h.position <= 3 ? 'p' + h.position : ''}">#${h.position}</span> dari ${h.total}`;
    sub = `${h.scans} scan \u00b7 ${num(h.avg)} g/scan`
      + (h.campusPosition ? ` \u00b7 Kampus #${h.campusPosition} dari ${h.campusTotal}` : '');
  } else if (h.status === 'few') {
    main = 'Belum masuk peringkat';
    sub = `${h.scans} scan (minimal ${min})`;
  } else {
    main = 'Tidak ada scan';
    sub = '';
  }
  return `<li class="wh ${h.status}">
    <span class="wh-date">${range}</span>
    <span class="wh-main">${main}</span>
    ${sub ? `<small class="wh-sub">${sub}</small>` : ''}
  </li>`;
}

function renderRankHistory() {
  const card = $('#rankHistoryCard');
  if (!card) return;
  const d = state.weeklyRanking;
  const hist = (d && d.history) || [];
  show(card, hist.length > 0);
  if (!hist.length) return;
  $('#rankHistoryNote').textContent =
    `Riwayat ${d.historyWeeks} minggu terakhir (sekitar 4 bulan), lengkap dengan tanggalnya.`;
  $('#rankHistory').innerHTML = hist.map(h => historyRow(h, d.minScans)).join('');
}

export function renderWeeklyRankingRecap() {
  const el = $('#weeklyRankingRecap');
  if (!el) return;
  const d = state.weeklyRanking;
  if (!d) { el.innerHTML = ''; renderRankHistory(); return; }

  const ranked = d.position != null;
  const campus = d.hasCampus && d.campusPosition
    ? ` \u00b7 Kampus #${d.campusPosition} dari ${d.campusTotal}` : '';
  const sub = ranked
    ? `dari ${d.totalUsers} pengguna minggu ini${campus}`
    : `Scanmu minggu ini: ${d.scans}. Minimal ${d.minScans} scan untuk masuk peringkat.`;

  el.innerHTML = `
    <div class="wk-top">
      <span class="wk-period">Minggu ${formatRange(d.weekStart, d.weekEnd)}</span>
      <span class="wk-live">Minggu berjalan</span>
    </div>
    <h2 class="wk-title">${ranked ? `Kamu peringkat ke-${d.position}!` : 'Kamu belum masuk peringkat'}</h2>
    <p class="wk-sub">${sub}</p>
    <p class="wk-msg ${esc(d.tone)}">${esc(d.message)}</p>
    ${d.liveNotice ? `<p class="wk-live-note">${ico('trophy')}<span>${esc(d.liveNotice)}</span></p>` : ''}
    ${d.top && d.top.length ? `
      <h3 class="wk-sec">Tiga teratas minggu ini</h3>
      <ol class="rank">${d.top.map(rowHtml).join('')}</ol>` : ''}
  `;
  renderRankHistory();
}

export function renderRank() {
  $$('#rankTabs .tab').forEach(t => t.setAttribute('aria-selected', t.dataset.r === state.rankTab));
  const tab = state.rank[state.rankTab];
  const list = $('#rankList'), empty = $('#rankEmpty');
  const note = $('#rankNote');
  if (note) note.textContent =
    `Diurutkan dari rata-rata emisi per scan paling rendah. Minimal ${minScans()} scan per minggu.`;

  if (tab.empty) {
    show(list, false); show(empty, true);
    const make = EMPTY[tab.empty] || EMPTY.no_data;
    empty.innerHTML = emptyCard({ ...make(tab), flat: true });
    return;
  }
  show(list, true); show(empty, false);
  list.innerHTML = tab.items.map((r, i, arr) => {
    const gap = r.is_me && i > 0 && r.pos > arr[i - 1].pos + 1
      ? '<li class="rank-gap" aria-hidden="true">\u22ef</li>' : '';
    return gap + rowHtml(r);
  }).join('');
}

$('#rankTabs').addEventListener('click', e => {
  const b = e.target.closest('[data-r]'); if (!b) return;
  state.rankTab = b.dataset.r; renderRank();
});
$('#shareBtn').addEventListener('click', () => toast('Kartu statistik siap dibagikan', 'share'));
$('#challengeBtn').addEventListener('click', () => toast('Pilih teman untuk ditantang', 'sword'));
