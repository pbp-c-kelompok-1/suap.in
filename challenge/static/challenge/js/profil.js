// Halaman Profil: grid avatar, tab jenis, edit & simpan profil
import { $, ico } from './utils.js';
import { SPECIALS, SPECIES } from './avatar-data.js';
import { TOTAL, avName, avatarIcon, avatarSvg, isLocked, isSp, levelReq, tabKey } from './avatar.js';
import { confetti, toast } from './fx.js';
import { mountMascots } from './mascot.js';
import { renderRank } from './laporan.js';
import { fmt, state } from './state.js';

const BADGE_STYLE = {
  scan_amount: { icon: 'camera', col: 'var(--green-500)', edge: 'var(--green-700)' },
  streak_duration: { icon: 'flame', col: 'var(--warn)', edge: '#B87400' },
};

/*
 * Satu mode edit untuk avatar, nama, dan bio.
 * Selama edit, avatar yang dipilih hanya pratinjau (state.pending).
 * Baru dipakai (state.avatar) setelah "Simpan perubahan" ditekan.
 */
let editingProfile = false;

function setProfileEditing(editing) {
  editingProfile = editing;
  $('#pName').disabled = !editing;
  $('#pBio').disabled = !editing;
  $('#avShuffle').disabled = !editing;
  $('#editProfile').hidden = editing;
  $('#cancelProfile').hidden = !editing;
  $('#saveProfile').hidden = !editing;
  $('#pickCard').classList.toggle('readonly', !editing);
  $('#profHint').textContent = editing
    ? 'Pilih avatar di sebelah, ubah nama & bio, lalu simpan sekaligus.'
    : 'Klik Edit profil untuk mengganti avatar, nama, dan bio.';
}

function renderStats() {
  const s = state.stats;
  $('#statsRow').innerHTML = `
    <div class="stat"><b>${s.scans}</b><span>Total scan</span></div>
    <div class="stat"><b>${s.recordStreak}</b><span>Streak terbaik (hari)</span></div>
    <div class="stat"><b>${fmt(s.avoidedKg).replace('.', ',')}</b><span>kg CO\u2082 di bawah budget</span></div>
    <div class="stat"><b>${s.campusRank ? '#' + s.campusRank : '\u2013'}</b><span>Peringkat kampus</span></div>`;
  $('#badgeRow').innerHTML = state.badges.length
    ? state.badges.map(b => {
        const st = BADGE_STYLE[b.type] || BADGE_STYLE.scan_amount;
        return b.earned
          ? `<div class="badge-i" title="${b.desc}" style="--col:${st.col};--edge:${st.edge}"><div class="bi">${ico(st.icon)}</div>${b.name}</div>`
          : `<div class="badge-i lock" title="${b.desc}"><div class="bi">${ico('lock')}</div>${b.name}</div>`;
      }).join('')
    : '<p class="muted">Belum ada lencana yang tersedia.</p>';
}

export function renderProfile() {
  renderStats();
  $('#pStreak').textContent = state.streak; $('#pLvl').textContent = state.level;
  const id = state.pending, locked = isLocked(id), sp = isSp(id);
  $('#avBig').innerHTML = avatarSvg(id, 'mascot');
  $('#avName').innerHTML = avName(id) + (sp ? ` <span class="sp-tag">${ico('star')}Spesial</span>` : '');
  $('#avMeta').textContent = locked
    ? `Terbuka di level ${levelReq(id)}`
    : sp ? SPECIALS[id - 100].d
    : id === state.avatar ? 'Dipakai sekarang'
    : editingProfile ? 'Belum disimpan' : 'Belum dipakai';

  /* avatar terkunci tidak boleh disimpan */
  $('#saveProfile').disabled = locked;

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

  /* Jangan menimpa input saat sedang edit; di mode lihat selalu ambil dari state. */
  if (!editingProfile) {
    $('#pName').value = state.profile.name || '';
    $('#pBio').value = state.profile.bio || '';
  }
  $('#bioCount').textContent = `${$('#pBio').value.length}/80`;
}

/* ---------- edit profil ---------- */
$('#editProfile').addEventListener('click', () => {
  state.pending = state.avatar;
  state.pTab = tabKey(state.avatar);
  setProfileEditing(true);
  renderProfile();
  $('#pName').focus();
});

$('#cancelProfile').addEventListener('click', () => {
  state.pending = state.avatar;   /* buang pratinjau avatar */
  setProfileEditing(false);
  renderProfile();                /* input diisi ulang dari state */
});

$('#saveProfile').addEventListener('click', () => {
  if (isLocked(state.pending)) return;
  const avatarChanged = state.pending !== state.avatar;

  /* Persistence ke database menunggu endpoint dari branch teman:
     kirim avatar + nama + bio dalam SATU request di sini. */
  state.profile.name = $('#pName').value.trim() || state.profile.name;
  state.profile.bio = $('#pBio').value.trim();
  state.avatar = state.pending;

  setProfileEditing(false);
  mountMascots(); renderProfile(); renderRank();
  if (avatarChanged) confetti(50, $('#avBig'));
  toast('Profil disimpan', 'check');
});

$('#pBio').addEventListener('input', () => { $('#bioCount').textContent = `${$('#pBio').value.length}/80`; });

/* ---------- pemilih avatar (hanya aktif saat edit) ---------- */
$('#spTabs').addEventListener('click', e => { const b = e.target.closest('[data-t]'); if (!b) return; state.pTab = b.dataset.t; renderProfile(); });
$('#avGrid').addEventListener('click', e => {
  if (!editingProfile) return;
  const b = e.target.closest('[data-av]'); if (!b) return;
  state.pending = +b.dataset.av; renderProfile();
});
$('#avShuffle').addEventListener('click', () => {
  if (!editingProfile) return;
  const pool = Array.from({ length: TOTAL }, (_, i) => i).filter(i => !isLocked(i) && i !== state.pending);
  if (!pool.length) return;
  state.pending = pool[Math.floor(Math.random() * pool.length)]; state.pTab = tabKey(state.pending); renderProfile();
});

/* kondisi awal: mode lihat */
setProfileEditing(false);
