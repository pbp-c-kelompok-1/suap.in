// Halaman Misi: header, misi harian, peti bonus. Semua dari data server.
import { $, ico } from './utils.js';
import { cheer } from './mascot.js';
import { confetti, toast } from './fx.js';
import { fmt, post, state, urls } from './state.js';
import { ACT, emptyCard } from './empty.js';
import { renderNotifs } from './notifikasi.js';

const done = q => q.val >= q.goal;
const doneCount = () => state.quests.filter(done).length;

export function renderHeader() {
  $('#streakNum').textContent = state.streak;
  $('#lvlNum').textContent = state.level;
  $('#freezeNum').textContent = state.freeze;
  $('#tierName').textContent = state.tier;
  const maxed = state.cap === 0;
  const pct = maxed ? 100 : Math.min(100, state.xp / state.cap * 100);
  $('#xpNum').textContent = maxed ? 'Level maksimal' : `${state.xp} / ${state.cap} XP`;
  $('#xpTrack').setAttribute('aria-valuenow', Math.round(pct));
  requestAnimationFrame(() => { $('#xpFill').style.width = pct + '%'; });

  const r = state.budget.used / state.budget.max;
  $('#ringVal').textContent = fmt(state.budget.used).replace('.', ',');
  $('#ringMax').textContent = `dari ${fmt(state.budget.max).replace('.', ',')} kg CO₂`;
  requestAnimationFrame(() => { $('#ringFg').style.strokeDashoffset = 314.16 * (1 - Math.min(1, r)); });

  const left = state.quests.length - doneCount();
  let bubble;
  if (state.totalScans === 0) bubble = `Belum ada scan!<small>Foto makanan pertamamu untuk mulai.</small>`;
  else if (state.scansToday === 0) bubble = `Belum scan hari ini.<small>Foto makananmu supaya streak tetap aman.</small>`;
  else if (left === 0) bubble = `Semua misi beres!<small>Buka petimu, lalu lanjut besok ya.</small>`;
  else bubble = `Tinggal ${left} misi lagi, ayo!<small>${state.budget.used > state.budget.max ? 'Budget karbonmu sudah terlewat hari ini.' : 'Budget karbonmu masih aman hari ini.'}</small>`;
  $('#bubble').innerHTML = bubble;
  $('#questCount').textContent = `${doneCount()}/${state.quests.length} selesai`;

  $('#misiEmpty').innerHTML = state.totalScans === 0
    ? emptyCard({
        title: 'Kamu belum pernah scan makanan',
        text: 'Scan makanan pertamamu untuk mulai mengumpulkan XP, streak, dan menyelesaikan misi.',
        actions: [ACT.scan(true), ACT.friends(false)],
      })
    : '';
}

export function renderQuests() {
  $('#quests').innerHTML = state.quests.map(q => {
    const ok = done(q);
    const pct = Math.min(100, q.val / q.goal * 100);
    const xp = q.xp || 0;
    const xpTag = xp ? `<span class="xp-tag">${ico('star')}+${xp} XP</span>` : '';
    let action;
    if (ok && q.claimed) action = `<button class="btn ok" disabled>${ico('check')}Diklaim</button>`;
    else if (ok) action = `<button class="btn ok" data-claim="${q.id}">${ico('gift')}Klaim +${xp} XP</button>`;
    else if (q.failed) action = `<button class="btn ghost sm" disabled>Lewat budget</button>`;
    else action = `<a class="btn ghost sm" href="${urls.scan}">${ico('camera')}Scan sekarang</a>`;
    return `
    <article class="raise quest tone-${q.tone} ${ok ? 'done' : ''} ${ok && !q.claimed ? 'ready' : ''}">
      <div class="q-ico">${ico(ok ? 'check' : q.icon)}</div>
      <div class="q-body">
        <h3>${q.title}</h3>
        <p>${q.desc}</p>
        <div class="prog"><div class="inset"><div class="bar" style="width:${pct}%"></div></div><b>${q.val}/${q.goal}</b></div>
        <span class="why">${ico('leaf')}${q.why}</span>
      </div>
      <div class="q-side">${xpTag}${action}</div>
    </article>`;
  }).join('');
}

export function renderChest() {
  const ready = state.chest.ready;
  const opened = state.chest.claimed;
  $('#chest').classList.toggle('open', opened);
  $('#chestTitle').textContent = opened ? 'Streak freeze didapat!' : ready ? 'Peti bonus siap dibuka' : 'Peti bonus terkunci';
  $('#chestDesc').textContent = opened
    ? `Kamu punya ${state.freeze} streak freeze. Streak aman kalau kamu skip 1 hari.`
    : ready ? 'Ketiga misi selesai. Ambil hadiahmu.' : 'Selesaikan ketiga misi untuk buka peti dan dapat 1 streak freeze.';
  const b = $('#chestBtn');
  b.disabled = !ready || opened;
  b.textContent = opened ? 'Sudah dibuka' : 'Buka peti';
}

$('#chestBtn').addEventListener('click', async () => {
  const btn = $('#chestBtn');
  btn.disabled = true;
  try {
    const res = await fetch(urls.claim, { method: 'POST', headers: { 'X-CSRFToken': urls.csrf }, credentials: 'same-origin' });
    const body = await res.json().catch(() => ({}));
    if (res.ok && body.ok) {
      state.chest.claimed = true;
      state.freeze = body.freezes;
      $('#freezeNum').textContent = state.freeze;
      confetti(80, btn); toast('Streak freeze +1', 'flame'); cheer();
    } else {
      toast(body.message || 'Gagal membuka peti.', 'alert');
    }
  } catch {
    toast('Tidak bisa terhubung ke server.', 'alert');
  }
  renderChest();
});

/* Klaim hadiah XP satu misi (manual, supaya user tahu apa yang didapat) */
$('#quests').addEventListener('click', async e => {
  const btn = e.target.closest('[data-claim]');
  if (!btn) return;
  const q = state.quests.find(x => x.id === btn.dataset.claim);
  if (!q || q.claimed) return;

  btn.disabled = true;
  let res;
  try {
    res = await post(urls.claimQuest, { quest_id: q.id });
  } catch {
    res = { ok: false, data: { message: 'Tidak bisa terhubung ke server.' } };
  }

  if (res.ok) {
    const d = res.data;
    q.claimed = true;
    state.xp = d.xpCurrent; state.cap = d.cap; state.level = d.level; state.tier = d.tier;
    if (d.notif) {
      const i = state.notifs.findIndex(n => n.id === d.notif.id);
      if (i >= 0) state.notifs[i] = d.notif;
      renderNotifs();
    }
    confetti(60, btn); cheer();
    toast(`+${d.xp} XP didapat dari "${q.title}"`, 'star');
    if (d.leveledUp) setTimeout(() => toast(`Naik ke level ${d.level}!`, 'trophy'), 1800);
  } else {
    toast(res.data.message || 'Gagal mengklaim hadiah.', 'alert');
    if (res.status === 400 && /sudah diklaim/.test(res.data.message || '')) q.claimed = true;
  }
  renderQuests();
  renderHeader();
});
