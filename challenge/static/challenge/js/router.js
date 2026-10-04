// Router hash (#/misi, #/laporan, ...)
import { $, $$ } from './utils.js';
import { animateBudgetRing } from './reference.js';
import { animateReport } from './laporan.js';
import { renderHeader } from './misi.js';
import { renderProfile } from './profil.js';
import { state } from './state.js';

/* ---------------- ROUTER ---------------- */
export function route() {
  const key = (location.hash.replace('#/', '') || 'misi');
  const page = ['misi', 'laporan', 'notifikasi', 'profil', 'auth', 'scanner'].includes(key) ? key : 'misi';
  $$('.page').forEach(p => p.classList.toggle('on', p.id === 'page-' + page));
  $$('.nav a').forEach(a => { if (a.dataset.page === page) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current'); });
  window.scrollTo({ top: 0 });
  if (page === 'laporan') animateReport();
  if (page === 'misi') { renderHeader(); }
  if (page === 'profil') { state.pending = state.avatar; renderProfile(); }
  if (page === 'scanner' && $('.tab[data-sub="budget"]').getAttribute('aria-selected') === 'true') animateBudgetRing();
}
window.addEventListener('hashchange', route);
