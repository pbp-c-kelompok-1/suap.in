// Helper DOM kecil ($, $$, ico)

export const $ = (s, r = document) => r.querySelector(s);
export const $$ = (s, r = document) => [...r.querySelectorAll(s)];
export const ico = (n, cls = '') => `<svg class="i ${cls}"><use href="#i-${n}"/></svg>`;

// Escape teks sebelum masuk innerHTML (nama pengguna & isi notifikasi bisa berasal dari user lain).
export const esc = s => String(s ?? '').replace(/[&<>"']/g, c => (
  { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
));
