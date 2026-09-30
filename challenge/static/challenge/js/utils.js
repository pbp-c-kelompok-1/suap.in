// Helper DOM kecil ($, $$, ico)

export const $ = (s, r = document) => r.querySelector(s);
export const $$ = (s, r = document) => [...r.querySelectorAll(s)];
export const ico = (n, cls = '') => `<svg class="i ${cls}"><use href="#i-${n}"/></svg>`;
