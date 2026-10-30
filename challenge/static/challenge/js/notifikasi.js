// Halaman Notifikasi: data & status baca/hapus disimpan di server.
import { $, $$, esc, ico } from './utils.js';
import { mountMascot } from './mascot.js';
import { post, state, urls } from './state.js';
import { ACT, emptyCard } from './empty.js';

export function renderNotifs() {
  $$('#filters .fchip').forEach(c => c.setAttribute('aria-pressed', c.dataset.f === state.filter));
  const list = state.notifs.filter(n => state.filter === 'all' || n.type === state.filter);
  const unread = state.notifs.filter(n => !n.read).length;
  const nb = $('#navBadge'); nb.textContent = unread; nb.hidden = unread === 0;
  $('#readAll').disabled = unread === 0;
  if (!list.length) {
    const none = state.notifs.length === 0;
    $('#notifs').innerHTML = emptyCard(none
      ? { title: 'Belum ada notifikasi', text: 'Kabar baru muncul setelah kamu scan makanan atau punya teman.',
          actions: [ACT.scan(true), ACT.friends(false)], mascotId: 'mascotEmpty' }
      : { title: 'Tidak ada notifikasi di kategori ini', text: 'Coba pilih kategori lain.', mascotId: 'mascotEmpty' });
    const mascotEl = $('#mascotEmpty');
    if (mascotEl) mountMascot(mascotEl, 'senyum');
    return;
  }
  $('#notifs').innerHTML = list.map(n => `
    <div class="n-wrap" data-id="${n.id}">
      <button class="notif ${n.read ? 'read' : ''}" data-open="${n.id}">
        <span class="n-ico tone-${n.tone}">${ico(n.ico)}</span>
        <span class="n-txt"><h3>${esc(n.t)}</h3><p>${esc(n.p)}</p></span>
        <span class="n-time">${n.time}</span>
        <span class="dot"></span>
      </button>
      <button class="del" data-del="${n.id}" aria-label="Hapus notifikasi">${ico('x')}</button>
    </div>`).join('');
}
/* Simpan ke server di latar belakang. Tampilan diperbarui dulu supaya terasa cepat. */
const sync = (url, body) => post(url, body).catch(() => { /* gagal jaringan: status baca akan disamakan saat halaman dimuat ulang */ });

$('#notifs').addEventListener('click', e => {
  const open = e.target.closest('[data-open]');
  const del = e.target.closest('[data-del]');
  if (open) {
    const n = state.notifs.find(x => x.id === open.dataset.open);
    if (!n) return;
    if (!n.read) { n.read = true; sync(urls.notifRead, { ids: [n.id] }); }
    renderNotifs();
    if (n.link) {
      if (n.link.startsWith('/')) location.href = n.link;   /* halaman lain, mis. daftar tantangan */
      else location.hash = n.link;                          /* mis. #/misi untuk klaim hadiah */
    }
  }
  if (del) {
    const id = del.dataset.del; const row = del.closest('.n-wrap');
    row.querySelector('.notif').classList.add('gone');
    sync(urls.notifDismiss, { id });
    setTimeout(() => { state.notifs = state.notifs.filter(x => x.id !== id); renderNotifs(); }, 240);
  }
});
$('#filters').addEventListener('click', e => {
  const c = e.target.closest('[data-f]'); if (!c) return;
  state.filter = c.dataset.f; renderNotifs();
});
$('#readAll').addEventListener('click', () => {
  state.notifs.forEach(n => n.read = true);
  sync(urls.notifRead, { all: true });
  renderNotifs();
});
