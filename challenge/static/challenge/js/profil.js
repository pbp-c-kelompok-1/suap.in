// Halaman Profil: grid avatar, tab jenis, simpan profil
import { $, ico } from './utils.js';
import { SPECIALS, SPECIES } from './avatar-data.js';
import { TOTAL, avName, avatarIcon, avatarSvg, isLocked, isSp, levelReq, tabKey } from './avatar.js';
import { confetti, toast } from './fx.js';
import { mountMascots } from './mascot.js';
import { renderRank } from './laporan.js';
import { state } from './state.js';

export function renderProfile() {
  $('#pStreak').textContent = state.streak; $('#pLvl').textContent = state.level;
  const id = state.pending, locked = isLocked(id), sp = isSp(id);
  $('#avBig').innerHTML = avatarSvg(id, 'mascot');
  $('#avName').innerHTML = avName(id) + (sp ? ` <span class="sp-tag">${ico('star')}Spesial</span>` : '');
  $('#avMeta').textContent = locked ? `Terbuka di level ${levelReq(id)}` : sp ? SPECIALS[id - 100].d : id === state.avatar ? 'Dipakai sekarang' : 'Belum dipakai';
  const use = $('#avUse'); use.disabled = locked || id === state.avatar;
  use.textContent = locked ? 'Terkunci' : id === state.avatar ? 'Sedang dipakai' : 'Pakai avatar ini';
  const all = Array.from({ length: TOTAL }, (_, i) => i);
  $('#avCount').textContent = `${all.filter(i => !isLocked(i)).length}/${TOTAL} terbuka`;

  $('#spTabs').innerHTML =
    `<button class="sptab allt" role="tab" aria-selected="${state.pTab === 'all'}" data-t="all">Semua</button>` +
    SPECIES.map((sp, i) => {
      const lk = !state.demoUnlock && state.level < sp.lv;
      return `<button class="sptab ${lk ? 'locked' : ''}" role="tab" aria-selected="${state.pTab === String(i)}" data-t="${i}"><span class="mini">${avatarIcon(i * 10)}</span>${sp.n}</button>`;
    }).join('') +
    `<button class="sptab sp-t" role="tab" aria-selected="${state.pTab === 'sp'}" data-t="sp"><span class="mini">${avatarIcon(100)}</span>Spesial</button>`;

  const bar = $('#lockBar');
  if (state.pTab === 'sp') {
    const got = SPECIALS.filter((_, i) => !isLocked(100 + i)).length;
    bar.hidden = false; bar.innerHTML = `${ico('star')}Makanan & minuman khas Indonesia. Terbuka bertahap, kamu sudah punya ${got} dari ${SPECIALS.length}.`;
  } else if (state.pTab !== 'all' && !state.demoUnlock && state.level < SPECIES[+state.pTab].lv) {
    bar.hidden = false; bar.innerHTML = `${ico('lock')}${SPECIES[+state.pTab].n} terbuka di level ${SPECIES[+state.pTab].lv}. Kamu sekarang Lv ${state.level}, tinggal ${SPECIES[+state.pTab].lv - state.level} level lagi.`;
  } else bar.hidden = true;

  const ids = state.pTab === 'all' ? all : state.pTab === 'sp' ? all.slice(100) : Array.from({ length: 10 }, (_, i) => +state.pTab * 10 + i);
  $('#avGrid').innerHTML = ids.map(i => {
    const lk = isLocked(i);
    return `<button class="av-cell ${lk ? 'locked' : ''} ${isSp(i) ? 'special' : ''}" data-av="${i}" aria-selected="${i === state.pending}" aria-label="${avName(i)}${lk ? ', terkunci' : ''}">${avatarIcon(i)}${isSp(i) ? ico('star', 'star') : ''}${lk ? `<span class="lk">${ico('lock')}<small>Lv ${levelReq(i)}</small></span>` : ''}${i === state.avatar ? `<span class="cur">${ico('check')}</span>` : ''}</button>`;
  }).join('');
  $('#pName').value = $('#pName').value || state.profile.name;
  $('#pBio').value = $('#pBio').value || state.profile.bio;
  $('#bioCount').textContent = `${$('#pBio').value.length}/80`;
}

$('#spTabs').addEventListener('click', e => { const b = e.target.closest('[data-t]'); if (!b) return; state.pTab = b.dataset.t; renderProfile(); });
$('#avGrid').addEventListener('click', e => { const b = e.target.closest('[data-av]'); if (!b) return; state.pending = +b.dataset.av; renderProfile(); });
$('#avUse').addEventListener('click', () => {
  state.avatar = state.pending; mountMascots(); renderProfile(); renderRank();
  confetti(50, $('#avUse')); toast('Avatar diganti', 'check');
});
$('#avShuffle').addEventListener('click', () => {
  const pool = Array.from({ length: TOTAL }, (_, i) => i).filter(i => !isLocked(i) && i !== state.pending);
  state.pending = pool[Math.floor(Math.random() * pool.length)]; state.pTab = tabKey(state.pending); renderProfile();
});
$('#avDemo').addEventListener('click', e => {
  state.demoUnlock = !state.demoUnlock;
  const b = e.currentTarget; b.setAttribute('aria-pressed', state.demoUnlock);
  b.querySelector('span').textContent = state.demoUnlock ? 'Mode demo: semua terbuka' : 'Buka semua (demo)';
  renderProfile();
});
$('#pBio').addEventListener('input', () => { $('#bioCount').textContent = `${$('#pBio').value.length}/80`; });
$('#saveProfile').addEventListener('click', () => {
  state.profile.name = $('#pName').value.trim() || state.profile.name;
  state.profile.bio = $('#pBio').value.trim();
  toast('Profil disimpan', 'check');
});
