// Halaman Misi: header, quest, peti bonus, XP
import { $, ico } from './utils.js';
import { cheer } from './mascot.js';
import { confetti, toast } from './fx.js';
import { fmt, state, tierFor } from './state.js';

function doneCount() { return state.quests.filter(q => q.claimed).length; }

export function renderHeader() {
  $('#streakNum').textContent = state.streak;
  $('#lvlNum').textContent = state.level;
  $('#tierName').textContent = tierFor(state.level);
  $('#xpNum').textContent = `${state.xp} / ${state.cap} XP`;
  $('#xpTrack').setAttribute('aria-valuenow', Math.round(state.xp / state.cap * 100));
  requestAnimationFrame(() => { $('#xpFill').style.width = Math.min(100, state.xp / state.cap * 100) + '%'; });
  const r = state.budget.used / state.budget.max;
  $('#ringVal').textContent = fmt(state.budget.used).replace('.', ',');
  requestAnimationFrame(() => { $('#ringFg').style.strokeDashoffset = 314.16 * (1 - Math.min(1, r)); });
  const left = 3 - doneCount();
  $('#bubble').innerHTML = left === 0
    ? `Semua misi beres!<small>Buka petimu, lalu lanjut besok ya.</small>`
    : `Tinggal ${left} misi lagi, ayo!<small>Budget karbonmu masih aman hari ini.</small>`;
  $('#questCount').textContent = `${doneCount()}/3 selesai`;
}

export function renderQuests() {
  $('#quests').innerHTML = state.quests.map(q => {
    const pct = Math.min(100, q.val / q.goal * 100);
    const ready = q.val >= q.goal && !q.claimed;
    const cls = `raise quest tone-${q.tone} ${q.claimed ? 'done' : ''} ${ready ? 'ready' : ''}`;
    let action;
    if (q.claimed) action = `<button class="btn ok" disabled>${ico('check')}Selesai</button>`;
    else if (ready) action = `<button class="btn ok" data-claim="${q.id}">Klaim hadiah</button>`;
    else action = `<button class="btn ghost sm" data-step="${q.id}">+ Catat progres</button>`;
    return `
    <article class="${cls}">
      <div class="q-ico">${ico(q.claimed ? 'check' : q.icon)}</div>
      <div class="q-body">
        <h3>${q.title}</h3>
        <p>${q.desc}</p>
        <div class="prog"><div class="inset"><div class="bar" style="width:${pct}%"></div></div><b>${q.val}/${q.goal}</b></div>
        <span class="why">${ico('leaf')}${q.why}</span>
      </div>
      <div class="q-side">
        <span class="xp-tag">+${q.xp} XP</span>
        ${action}
      </div>
    </article>`;
  }).join('');
}

export function renderChest() {
  const all = doneCount() === 3;
  const c = $('#chest');
  c.classList.toggle('open', state.chestOpen);
  $('#chestTitle').textContent = state.chestOpen ? 'Streak freeze didapat!' : all ? 'Peti bonus siap dibuka' : 'Peti bonus terkunci';
  $('#chestDesc').textContent = state.chestOpen
    ? `Kamu punya ${state.freeze + 0} streak freeze. Streak aman kalau kamu skip 1 hari.`
    : all ? 'Ketiga misi selesai. Ambil hadiahmu.' : 'Selesaikan ketiga misi untuk buka peti dan dapat 1 streak freeze.';
  const b = $('#chestBtn');
  b.disabled = !all || state.chestOpen;
  b.textContent = state.chestOpen ? 'Sudah dibuka' : 'Buka peti';
}

function addXp(n) {
  state.xp += n;
  while (state.xp >= state.cap) { state.xp -= state.cap; state.level++; state.cap += 50; toast(`Naik ke level ${state.level}!`); confetti(60); }
  renderHeader();
}

$('#quests').addEventListener('click', e => {
  const step = e.target.closest('[data-step]');
  const claim = e.target.closest('[data-claim]');
  if (step) {
    const q = state.quests.find(x => x.id == step.dataset.step);
    q.val = Math.min(q.goal, q.val + 1);
    if (q.val >= q.goal) cheer();
  }
  if (claim) {
    const q = state.quests.find(x => x.id == claim.dataset.claim);
    q.claimed = true;
    confetti(36, claim);
    toast(`+${q.xp} XP`, 'leaf');
    cheer();
    addXp(q.xp);
  }
  renderQuests(); renderChest(); renderHeader();
});
$('#chestBtn').addEventListener('click', () => {
  state.chestOpen = true; state.freeze++; confetti(80, $('#chestBtn')); toast('Streak freeze +1', 'flame');
  renderChest();
});
