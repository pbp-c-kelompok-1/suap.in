// Halaman Laporan: grafik mingguan + peringkat
import { $, $$ } from './utils.js';
import { avatarIcon } from './avatar.js';
import { fmt, state } from './state.js';
import { toast } from './fx.js';

const CAP = 3.5;
export function renderReport() {
  const max = 4.2;
  const best = Math.min(...state.weekly.map(w => w.v));
  $('#bars').innerHTML =
    `<div class="cap" style="bottom:calc(${CAP / max * 100}% * .88 + 28px)"><span>Budget ${fmt(CAP).replace('.', ',')}</span></div>` +
    state.weekly.map(w => {
      const cls = w.v > CAP ? 'over' : w.v === best ? 'best' : '';
      return `<div class="col" role="listitem"><button class="pillar ${cls}" data-h="${w.v / max * 100}" aria-label="${w.d}: ${w.v} kg CO₂"><span class="tip">${fmt(w.v).replace('.', ',')} kg</span></button><small>${w.d}</small></div>`;
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
