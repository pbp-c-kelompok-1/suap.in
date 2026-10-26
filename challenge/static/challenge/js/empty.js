// Kartu "belum ada data" + tombol alternatif, dipakai semua halaman.
import { ico } from './utils.js';
import { urls } from './state.js';

export const ACT = {
  scan:    (primary = true) => ({ href: urls.scan,    label: 'Scan makanan', icon: 'camera',  primary }),
  friends: (primary = false) => ({ href: urls.friends, label: 'Cari teman',  icon: 'userplus', primary }),
  campus:  (primary = true) => ({ href: urls.campus,  label: 'Pilih kampus', icon: 'building', primary }),
};

export function emptyCard({ title, text, actions = [], mascotId = '', flat = false }) {
  const btns = actions.map(a =>
    `<a class="btn ${a.primary ? 'ok' : 'ghost'}" href="${a.href}">${ico(a.icon)}${a.label}</a>`).join('');
  return `<div class="${flat ? 'empty' : 'raise empty'}">
    ${mascotId ? `<div class="mascot-wrap" id="${mascotId}"></div>` : ''}
    <h3>${title}</h3><p>${text}</p>
    ${btns ? `<div class="empty-actions">${btns}</div>` : ''}
  </div>`;
}
