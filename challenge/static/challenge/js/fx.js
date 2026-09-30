// Efek: toast & confetti
import { $, ico } from './utils.js';

let toastT;
export function toast(msg, icon = 'check') {
  const t = $('#toast'); t.innerHTML = ico(icon) + msg; t.classList.add('show');
  clearTimeout(toastT); toastT = setTimeout(() => t.classList.remove('show'), 1800);
}
export function confetti(n = 40, origin) {
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const r = origin ? origin.getBoundingClientRect() : { left: innerWidth / 2, top: innerHeight / 3, width: 0, height: 0 };
  const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
  const cols = ['#00E676', '#0DA69B', '#2F80ED', '#F5A623', '#74ACFF', '#63D68C'];
  for (let i = 0; i < n; i++) {
    const p = document.createElement('i'); p.className = 'confetti';
    const a = Math.random() * Math.PI * 2, d = 90 + Math.random() * 190;
    p.style.cssText = `left:${cx}px;top:${cy}px;background:${cols[i % cols.length]};--x:${Math.cos(a) * d}px;--y:${Math.sin(a) * d + 120}px;--r:${Math.random() * 720 - 360}deg;--d:${900 + Math.random() * 700}ms`;
    document.body.appendChild(p); setTimeout(() => p.remove(), 1700);
  }
}
