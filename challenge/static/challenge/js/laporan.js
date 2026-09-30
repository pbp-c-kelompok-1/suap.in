// Halaman Laporan: grafik mingguan + peringkat
import { $, $$ } from './utils.js';
import { avatarIcon } from './avatar.js';
import { fmt, state } from './state.js';
import { toast } from './fx.js';

export function renderReport() {
  const cap = state.budgetCapKg;
  const withData = state.weekly.filter(w => w.hasData);
  const best = withData.length ? Math.min(...withData.map(w => w.v)) : null;
  const max = Math.max(cap, ...state.weekly.map(w => w.v), 0.1) * 1.2;
  $('#bars').innerHTML =
    `<div class="cap" style="bottom:calc(${cap / max * 100}% * .88 + 28px)"><span>Budget ${fmt(cap).replace('.', ',')}</span></div>` +
    state.weekly.map(w => {
      const cls = !w.hasData ? 'nodata' : w.v > cap ? 'over' : w.v === best ? 'best' : '';
      const label = w.hasData ? `${w.d}: ${fmt(w.v).replace('.', ',')} kg CO₂` : `${w.d}: belum ada data`;
      const tip = w.hasData ? `${fmt(w.v).replace('.', ',')} kg` : 'Belum ada data';
      return `<div class="col" role="listitem"><button class="pillar ${cls}" data-h="${w.hasData ? w.v / max * 100 : 4}" aria-label="${label}"><span class="tip">${tip}</span></button><small>${w.d}</small></div>`;
    }).join('');
}
export function animateReport() {
  // total counter
  const total = state.weekly.reduce((a, b) => a + b.v, 0);
  const el = $('#weekTotal'); const t0 = performance.now();
  (function tick(t) {
    const p = Math.min(1, (t - t0) / 900), e = 1 - Math.pow(1 - p, 3);
    el.textContent = fmt(total * e).replace('.', ',');
    if (p < 1) requestAnimationFrame(tick);
  })(t0);
  // bars
  $$('.pillar').forEach((b, i) => { b.style.height = '0'; setTimeout(() => { b.style.height = `calc(${b.dataset.h}% * .88)`; }, 80 + i * 70); });
}
const avColors = ['var(--teal-500)', 'var(--blue-500)', 'var(--green-500)', 'var(--warn)', 'var(--blue-700)'];
export function renderRank() {
  $$('#rankTabs .tab').forEach(t => t.setAttribute('aria-selected', t.dataset.r === state.rankTab));
  $('#rankList').innerHTML = state.rank[state.rankTab].map((r, i) => `
    <li class="${r[2] ? 'me' : ''}">
      <span class="pos ${i < 3 ? 'p' + (i + 1) : ''}">${i + 1}</span>
      ${r[2] ? `<span class="av avme">${avatarIcon(state.avatar)}</span>` : `<span class="av" style="background:${avColors[i % 5]}">${r[0][0]}</span>`}
      <span class="nm">${r[0]}</span>
      <span class="co">${fmt(r[1]).replace('.', ',')} <small>kg CO₂</small></span>
    </li>`).join('');
}
$('#rankTabs').addEventListener('click', e => {
  const b = e.target.closest('[data-r]'); if (!b) return;
  state.rankTab = b.dataset.r; renderRank();
});
$('#shareBtn').addEventListener('click', () => toast('Kartu statistik siap dibagikan', 'share'));
$('#challengeBtn').addEventListener('click', () => toast('Pilih teman untuk ditantang', 'sword'));
