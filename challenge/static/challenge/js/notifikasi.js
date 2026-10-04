// Halaman Notifikasi: filter + tandai dibaca
import { $, $$, ico } from './utils.js';
import { avatarSvg } from './avatar.js';
import { state } from './state.js';

export function renderNotifs() {
  $$('#filters .fchip').forEach(c => c.setAttribute('aria-pressed', c.dataset.f === state.filter));
  const list = state.notifs.filter(n => state.filter === 'all' || n.type === state.filter);
  const unread = state.notifs.filter(n => !n.read).length;
  const nb = $('#navBadge'); nb.textContent = unread; nb.hidden = unread === 0;
  $('#readAll').disabled = unread === 0;
  if (!list.length) {
    $('#notifs').innerHTML = `<div class="raise empty"><div class="mascot-wrap" id="mascotEmpty"></div><h3>Tidak ada notifikasi</h3><p>Semua bersih. Foto makananmu untuk memancing kabar baru.</p></div>`;
    $('#mascotEmpty').innerHTML = avatarSvg(state.avatar, 'mascot');
    return;
  }
  $('#notifs').innerHTML = list.map(n => `
    <div class="n-wrap" data-id="${n.id}">
      <button class="notif ${n.read ? 'read' : ''}" data-open="${n.id}">
        <span class="n-ico tone-${n.tone}">${ico(n.ico)}</span>
        <span class="n-txt"><h3>${n.t}</h3><p>${n.p}</p></span>
        <span class="n-time">${n.time}</span>
        <span class="dot"></span>
      </button>
      <button class="del" data-del="${n.id}" aria-label="Hapus notifikasi">${ico('x')}</button>
    </div>`).join('');
}
$('#notifs').addEventListener('click', e => {
  const open = e.target.closest('[data-open]');
  const del = e.target.closest('[data-del]');
  if (open) { const n = state.notifs.find(x => x.id == open.dataset.open); n.read = true; renderNotifs(); }
  if (del) {
    const id = del.dataset.del; const row = del.closest('.n-wrap');
    row.querySelector('.notif').classList.add('gone');
    setTimeout(() => { state.notifs = state.notifs.filter(x => x.id != id); renderNotifs(); }, 240);
  }
});
$('#filters').addEventListener('click', e => {
  const c = e.target.closest('[data-f]'); if (!c) return;
  state.filter = c.dataset.f; renderNotifs();
});
$('#readAll').addEventListener('click', () => { state.notifs.forEach(n => n.read = true); renderNotifs(); });
