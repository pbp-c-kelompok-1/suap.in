// Referensi modul lain: Autentikasi & Scanner
import { $, $$, ico } from './utils.js';
import { avatarSvg } from './avatar.js';
import { state } from './state.js';
import { toast } from './fx.js';

export function initSubTabs(pageSel, tabsSel) {
  $(tabsSel).addEventListener('click', e => {
    const b = e.target.closest('[data-sub]'); if (!b) return;
    $$(tabsSel + ' .tab').forEach(t => t.setAttribute('aria-selected', t === b ? 'true' : 'false'));
    $$(pageSel + ' .subpage').forEach(sp => { sp.hidden = sp.dataset.sub !== b.dataset.sub; });
    window.scrollTo({ top: 0 });
    if (b.dataset.sub === 'budget') animateBudgetRing();
  });
}
function gotoSub(tabsSel, key) {
  const b = $(tabsSel + ' [data-sub="' + key + '"]'); if (b) b.click();
}
$('#page-auth').addEventListener('click', e => {
  const b = e.target.closest('[data-goto]'); if (!b) return; e.preventDefault();
  gotoSub('#authTabs', b.dataset.goto);
});
$('#page-scanner').addEventListener('click', e => {
  const b = e.target.closest('[data-goto2]'); if (!b) return;
  gotoSub('#scanTabs', b.dataset.goto2);
  if (b.dataset.goto2 === 'log') toast('Tersimpan ke log harian', 'check');
});
$('#doScan').addEventListener('click', () => { gotoSub('#scanTabs', 'hasil'); toast('Foto berhasil dipindai', 'camera'); });

// password show/hide
document.addEventListener('click', e => {
  const b = e.target.closest('.eye-btn'); if (!b) return;
  const inp = document.getElementById(b.dataset.toggle); if (!inp) return;
  const show = inp.type === 'password';
  inp.type = show ? 'text' : 'password';
  b.innerHTML = `<svg class="i"><use href="#i-${show ? 'eye-off' : 'eye'}"/></svg>`;
});

// password strength
const rp = $('#regPass');
if (rp) rp.addEventListener('input', () => {
  const v = rp.value; let s = 0;
  if (v.length >= 8) s++; if (/[A-Z]/.test(v)) s++; if (/[0-9]/.test(v)) s++; if (/[^A-Za-z0-9]/.test(v)) s++;
  const pct = [0, 25, 50, 75, 100][v.length ? s + 1 : 0];
  const cols = ['var(--danger)', 'var(--danger)', 'var(--warn)', 'var(--teal-500)', 'var(--ok)'];
  const lbls = ['Kekuatan sandi', 'Lemah', 'Cukup', 'Kuat', 'Sangat kuat'];
  $('#strengthBar').style.width = pct + '%'; $('#strengthBar').style.background = cols[v.length ? s + 1 : 0];
  $('#strengthLbl').textContent = lbls[v.length ? s + 1 : 0];
});

// profil publik: lihat sebagai kamu / teman
export function renderPubProfile(view) {
  $$('#viewAsTabs .tab').forEach(t => t.setAttribute('aria-selected', t.dataset.view === view));
  $('#pubAvatarIcon').innerHTML = avatarSvg(view === 'me' ? state.avatar : 4);
  $('#pubName').textContent = view === 'me' ? state.profile.name : 'Dinda Ayu Kirana';
  $('#pubUni').textContent = view === 'me' ? 'Universitas Indonesia' : 'Universitas Diponegoro';
  $('#pubActions').innerHTML = view === 'me'
    ? `<button class="btn ghost sm" data-goto="daftar">${ico('edit')}Edit Profil</button><button class="btn sm" onclick="location.hash='#/profil'">${ico('user')}Ubah Avatar</button>`
    : `<button class="btn ok sm">${ico('userplus')}Tambah Teman</button><button class="btn ghost sm">${ico('sword')}Tantang</button>`;
}
$('#viewAsTabs').addEventListener('click', e => { const b = e.target.closest('[data-view]'); if (b) renderPubProfile(b.dataset.view); });

// halaman avatar: kondisi Sehat/Waspada/Layu
const COND = {
  sehat: { cls: 'ok', label: 'Kondisi: Sehat', desc: 'Streak terjaga dan budget karbon aman. Avatarmu tumbuh subur.', op: 1 },
  waspada: { cls: 'warn', label: 'Kondisi: Waspada', desc: 'Streak sempat putus atau budget karbon sering lewat. Avatar mulai layu, perbaiki sebelum turun tingkat.', op: .75 },
  layu: { cls: 'bad', label: 'Kondisi: Layu', desc: 'Streak lama tidak jalan dan emisi tinggi. Avatar kehilangan progres kalau dibiarkan terus.', op: .4 },
};
export function renderCond(key) {
  $$('#condTabs .ctab').forEach(t => t.setAttribute('aria-pressed', t.dataset.cond === key));
  const c = COND[key];
  const st = $('#avoStatus'); st.className = 'avo-status ' + c.cls; st.innerHTML = ico(c.cls === 'ok' ? 'check' : 'alert') + c.label;
  $('#avoDesc').textContent = c.desc;
  const m = $('#avoBig .mascot'); if (m) m.style.opacity = c.op;
}
$('#condTabs').addEventListener('click', e => { const b = e.target.closest('[data-cond]'); if (b) renderCond(b.dataset.cond); });

// budget karbon: ring + mini bars per waktu makan
export function animateBudgetRing() {
  requestAnimationFrame(() => { $('#budgetRingFg').style.strokeDashoffset = 314.16 * (1 - 2.1 / 3.5); });
  const meals = [{ n: 'Sarapan', v: .8, max: 1.2 }, { n: 'Siang', v: .9, max: 1.2 }, { n: 'Malam', v: .4, max: 1.1 }];
  $('#miniBars').innerHTML = meals.map(m => `
    <div class="mbar"><div class="inset"><div class="fill" data-h="${Math.min(100, m.v / m.max * 100)}"></div></div><b>${m.v.toFixed(1).replace('.', ',')} kg</b><span>${m.n}</span></div>`).join('');
  $$('#miniBars .fill').forEach((f, i) => setTimeout(() => { f.style.height = f.dataset.h + '%'; }, 100 + i * 100));
}
