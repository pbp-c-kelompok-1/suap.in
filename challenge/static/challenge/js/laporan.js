// Halaman Laporan: grafik mingguan + peringkat. Semua dari data server.
import { $, $$ } from './utils.js';
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

const EMPTY = {
  no_friends: () => ({
    title: 'Kamu belum punya teman',
    text: 'Tambah teman untuk adu emisi tiap minggu, atau scan makananmu dulu.',
    actions: [ACT.friends(true), ACT.scan(false)],
  }),
  no_campus: () => ({
    title: 'Kamu belum memilih kampus',
    text: 'Pilih kampusmu untuk melihat peringkat teman satu kampus.',
    actions: [ACT.campus(true), ACT.scan(false)],
  }),
  no_data: () => ({
    title: 'Belum ada yang scan minggu ini',
    text: 'Scan makanan pertamamu untuk masuk peringkat, atau ajak temanmu.',
    actions: [ACT.scan(true), ACT.friends(false)],
  }),
};

const avColors = ['var(--teal-500)', 'var(--blue-500)', 'var(--green-500)', 'var(--warn)', 'var(--blue-700)'];
export function renderRank() {
  $$('#rankTabs .tab').forEach(t => t.setAttribute('aria-selected', t.dataset.r === state.rankTab));
  const tab = state.rank[state.rankTab];
  const list = $('#rankList'), empty = $('#rankEmpty');
  if (tab.empty) {
    show(list, false); show(empty, true);
    empty.innerHTML = emptyCard({ ...EMPTY[tab.empty](), flat: true });
    return;
  }
  show(list, true); show(empty, false);
  list.innerHTML = tab.items.map((r, i) => `
    <li class="${r.is_me ? 'me' : ''}">
      <span class="pos ${r.pos <= 3 ? 'p' + r.pos : ''}">${r.pos}</span>
      ${r.is_me ? `<span class="av avme">${avatarIcon(state.avatar)}</span>` : `<span class="av" style="background:${avColors[i % 5]}">${(r.name[0] || '?').toUpperCase()}</span>`}
      <span class="nm">${r.is_me ? 'Kamu' : r.name}</span>
      <span class="co">${fmt(r.kg).replace('.', ',')} <small>kg CO₂</small></span>
    </li>`).join('');
}
$('#rankTabs').addEventListener('click', e => {
  const b = e.target.closest('[data-r]'); if (!b) return;
  state.rankTab = b.dataset.r; renderRank();
});
$('#shareBtn').addEventListener('click', () => toast('Kartu statistik siap dibagikan', 'share'));
$('#challengeBtn').addEventListener('click', () => toast('Pilih teman untuk ditantang', 'sword'));
