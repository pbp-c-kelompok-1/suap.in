// Maskot di hero halaman Misi
import { $ } from './utils.js';
import { avatarSvg } from './avatar.js';
import { state } from './state.js';

export function mountMascots() {
  $('#mascotHero').innerHTML = avatarSvg(state.avatar, 'mascot');
}
export function cheer() {
  const m = $('#mascotHero .mascot'); if (!m) return;
  m.classList.remove('cheer'); void m.offsetWidth; m.classList.add('cheer');
}
