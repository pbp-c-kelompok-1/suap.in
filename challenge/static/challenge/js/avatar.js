// Helper avatar: nama, level minimal, status terkunci, render SVG
import { BODY, FACE, PAL, SPECIALS, SPECIES, cheeks } from './avatar-data.js';
import { state } from './state.js';

export const TOTAL = 100 + SPECIALS.length;
export const isSp = id => id >= 100;
export const levelReq = id => isSp(id) ? SPECIALS[id - 100].lv : SPECIES[Math.floor(id / 10)].lv;
export const tabKey = id => isSp(id) ? 'sp' : String(Math.floor(id / 10));
export const avName = id => isSp(id) ? SPECIALS[id - 100].n : `${SPECIES[Math.floor(id / 10)].n} ${PAL[id % 10].n}`;
export const isLocked = id => !state.demoUnlock && state.level < levelReq(id);
export function avatarSvg(id, cls = '') {
  const sp = isSp(id);
  const d = sp ? SPECIALS[id - 100].draw() : BODY[Math.floor(id / 10)](PAL[id % 10]);
  const f = sp ? SPECIALS[id - 100].f : (Math.floor(id / 10) * 7 + (id % 10) * 3) % 10;
  return `<svg class="${cls}" viewBox="0 0 120 120" role="img" aria-label="${avName(id)}"><ellipse cx="60" cy="114" rx="30" ry="4.5" fill="#000" opacity=".1"/>${d.svg}<g transform="translate(${d.x} ${d.y}) scale(${d.s})">${FACE[f]}${cheeks}</g></svg>`;
}
export const avatarIcon = id => avatarSvg(id).replace('role="img"', 'aria-hidden="true"');
