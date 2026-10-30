// Maskot di hero halaman Misi
import { $ } from './utils.js';

export function mountMascot(slot, pose = 'senyum') {
    const template = document.getElementById('es-mascot-tpl');
    if (!slot || !template) return;

    // Salin template supaya gambarnya bisa dipakai di beberapa tempat.
    const mascot = template.content.cloneNode(true);
    const image = mascot.querySelector('img');

    image.src = template.dataset[pose] || image.src;
    slot.replaceChildren(mascot);
}

export function mountMascots() {
    mountMascot($('#mascotHero'), 'menyapa');
}

export function cheer() {
    const mascot = $('#mascotHero .mascot');
    if (!mascot) return;

    // Ulangi animasinya kalau dipanggil lagi.
    mascot.classList.remove('cheer');
    void mascot.offsetWidth;
    mascot.classList.add('cheer');
}