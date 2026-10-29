// Kartu statistik mingguan (gambar) + pilihan tujuan bagikan.
// Gambar dibuat di browser dengan canvas, jadi tidak butuh server atau pustaka tambahan.
import { toast } from './fx.js';

const W = 1080, H = 1920;
const FONT = "'Fredoka', 'Nunito', system-ui, sans-serif";

const kgText = n => Number(n || 0).toLocaleString('id-ID', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const intText = n => Number(n || 0).toLocaleString('id-ID');

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

function text(ctx, str, x, y, { size = 40, weight = 600, color = '#0F2A24', align = 'left' } = {}) {
  ctx.font = `${weight} ${size}px ${FONT}`;
  ctx.fillStyle = color;
  ctx.textAlign = align;
  ctx.textBaseline = 'alphabetic';
  ctx.fillText(str, x, y);
}

function leaf(ctx, cx, cy, s, color) {
  ctx.save();
  ctx.translate(cx, cy);
  ctx.scale(s, s);
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(0, -30);
  ctx.bezierCurveTo(34, -22, 34, 22, 0, 30);
  ctx.bezierCurveTo(-34, 22, -34, -22, 0, -30);
  ctx.fill();
  ctx.restore();
}

// d: { name, range, position, total, campusPosition, campusTotal, kg, scans, avg, weekly[], cap }
export function renderShareCard(d) {
  const canvas = document.createElement('canvas');
  canvas.width = W; canvas.height = H;
  const ctx = canvas.getContext('2d');

  const bg = ctx.createLinearGradient(0, 0, W, H);
  bg.addColorStop(0, '#0B8F86');
  bg.addColorStop(1, '#1EA854');
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, W, H);

  // lingkaran dekoratif
  ctx.fillStyle = 'rgba(255,255,255,.08)';
  ctx.beginPath(); ctx.arc(960, 220, 260, 0, Math.PI * 2); ctx.fill();
  ctx.beginPath(); ctx.arc(80, 1700, 320, 0, Math.PI * 2); ctx.fill();

  // header
  roundRect(ctx, 80, 90, 96, 96, 28); ctx.fillStyle = '#FFFFFF'; ctx.fill();
  leaf(ctx, 128, 138, 1.15, '#0B8F86');
  text(ctx, 'Suap.in', 200, 160, { size: 72, weight: 700, color: '#FFFFFF' });
  text(ctx, 'Laporan mingguan', 80, 290, { size: 44, weight: 500, color: 'rgba(255,255,255,.85)' });
  text(ctx, d.range, 80, 360, { size: 62, weight: 700, color: '#FFFFFF' });

  // panel utama
  roundRect(ctx, 60, 430, W - 120, 1210, 56); ctx.fillStyle = '#FFFFFF'; ctx.fill();

  text(ctx, d.name, 120, 530, { size: 46, weight: 600, color: '#4B6660' });

  const ranked = d.position != null;
  if (ranked) {
    text(ctx, 'Peringkat', 120, 650, { size: 56, weight: 500, color: '#4B6660' });
    text(ctx, String(d.position), 120, 860, { size: 230, weight: 700, color: '#0B8F86' });
    const numW = ctx.measureText(String(d.position)).width;
    text(ctx, `dari ${intText(d.total)} pengguna`, 120 + numW + 36, 860, { size: 52, weight: 600, color: '#0F2A24' });
    if (d.campusPosition) {
      text(ctx, `Kampus: peringkat ${d.campusPosition} dari ${intText(d.campusTotal)}`, 120, 940, { size: 46, weight: 600, color: '#4B6660' });
    }
  } else {
    text(ctx, 'Pejuang rendah karbon', 120, 700, { size: 76, weight: 700, color: '#0B8F86' });
    text(ctx, 'Sedang mengumpulkan scan pertama', 120, 780, { size: 46, weight: 500, color: '#4B6660' });
  }

  // tiga angka utama
  const boxes = [
    [`${kgText(d.kg)}`, 'kg CO\u2082 minggu ini'],
    [`${intText(d.scans)}`, 'scan makanan'],
    [`${intText(d.avg)}`, 'g CO\u2082 per scan'],
  ];
  const bw = 260, gap = 30, bx0 = 120, by = 1010;   // 3 kotak + 2 celah = 840 = lebar isi panel
  boxes.forEach(([big, small], i) => {
    const x = bx0 + i * (bw + gap);
    roundRect(ctx, x, by, bw, 220, 36); ctx.fillStyle = '#EAF7F2'; ctx.fill();
    text(ctx, big, x + bw / 2, by + 110, { size: 74, weight: 700, color: '#0F2A24', align: 'center' });
    text(ctx, small, x + bw / 2, by + 168, { size: 27, weight: 600, color: '#4B6660', align: 'center' });
  });

  // grafik 7 hari
  text(ctx, 'Emisi harian', 120, 1320, { size: 40, weight: 600, color: '#4B6660' });
  const weekly = d.weekly || [];
  const cap = d.cap || 2;
  const maxV = Math.max(cap, ...weekly.map(w => w.v), 0.1) * 1.15;
  const chartTop = 1350, chartH = 190, chartL = 120, chartW = W - 240;
  const colW = chartW / 7;
  weekly.forEach((w, i) => {
    const cx = chartL + colW * i + colW / 2;
    const bwid = 70;
    if (w.hasData) {
      const h = Math.max(10, (w.v / maxV) * chartH);
      ctx.fillStyle = w.v > cap ? '#E5484D' : '#1EA854';
      roundRect(ctx, cx - bwid / 2, chartTop + chartH - h, bwid, h, 16); ctx.fill();
    } else {
      ctx.fillStyle = '#E3EFEA';
      roundRect(ctx, cx - bwid / 2, chartTop + chartH - 10, bwid, 10, 5); ctx.fill();
    }
    text(ctx, w.d, cx, chartTop + chartH + 44, { size: 30, weight: 600, color: '#4B6660', align: 'center' });
  });
  const capY = chartTop + chartH - (cap / maxV) * chartH;
  ctx.setLineDash([14, 10]); ctx.strokeStyle = '#F5A623'; ctx.lineWidth = 4;
  ctx.beginPath(); ctx.moveTo(chartL, capY); ctx.lineTo(chartL + chartW, capY); ctx.stroke();
  ctx.setLineDash([]);

  // footer
  text(ctx, 'Yuk kurangi jejak karbon', W / 2, 1760, { size: 54, weight: 700, color: '#FFFFFF', align: 'center' });
  text(ctx, 'dari makanan sehari-hari.', W / 2, 1830, { size: 54, weight: 700, color: '#FFFFFF', align: 'center' });

  return canvas;
}

export function shareText(d, url) {
  const base = d.position != null
    ? `Minggu ${d.range}: aku peringkat ${d.position} dari ${intText(d.total)} pengguna di Suap.in, rata-rata ${intText(d.avg)} g CO\u2082 per scan.`
    : `Laporan mingguanku di Suap.in (${d.range}): ${kgText(d.kg)} kg CO\u2082 dari ${intText(d.scans)} scan.`;
  return `${base} Yuk ikut kurangi jejak karbon makananmu!`;
}

const enc = encodeURIComponent;

function targets(msg, url) {
  return [
    { id: 'wa', label: 'WhatsApp', color: '#25D366', mark: 'WA', href: `https://wa.me/?text=${enc(`${msg} ${url}`)}` },
    { id: 'x', label: 'X', color: '#111111', mark: 'X', href: `https://twitter.com/intent/tweet?text=${enc(msg)}&url=${enc(url)}` },
    { id: 'threads', label: 'Threads', color: '#222222', mark: '@', href: `https://www.threads.net/intent/post?text=${enc(`${msg} ${url}`)}` },
    { id: 'tg', label: 'Telegram', color: '#2AA3E0', mark: 'TG', href: `https://t.me/share/url?url=${enc(url)}&text=${enc(msg)}` },
    { id: 'fb', label: 'Facebook', color: '#1877F2', mark: 'f', href: `https://www.facebook.com/sharer/sharer.php?u=${enc(url)}` },
  ];
}

const toBlob = canvas => new Promise(res => canvas.toBlob(res, 'image/png'));

function download(blob, name) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = name;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}

async function copyText(str) {
  try {
    await navigator.clipboard.writeText(str);
    return true;
  } catch {
    const ta = document.createElement('textarea');
    ta.value = str; ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    let ok = false;
    try { ok = document.execCommand('copy'); } catch { /* diabaikan */ }
    ta.remove();
    return ok;
  }
}

let openModal = null;

export async function openShare(d, opener) {
  if (openModal) return;
  if (document.fonts && document.fonts.ready) { try { await document.fonts.ready; } catch { /* diabaikan */ } }

  const url = `${location.origin}/`;
  const msg = shareText(d, url);
  const canvas = renderShareCard(d);
  const blob = await toBlob(canvas);
  const file = blob ? new File([blob], 'laporan-suapin.png', { type: 'image/png' }) : null;
  const canNativeFile = !!(file && navigator.canShare && navigator.canShare({ files: [file] }));
  const canNative = !!navigator.share;

  const root = document.createElement('div');
  root.className = 'share-modal';
  root.innerHTML = `
    <div class="share-sheet" role="dialog" aria-modal="true" aria-labelledby="shareTitle">
      <button type="button" class="share-close" aria-label="Tutup">\u00d7</button>
      <h3 id="shareTitle">Bagikan laporanmu</h3>
      <div class="share-preview"></div>
      ${canNative ? '<button type="button" class="btn ok wide" data-act="native">Bagikan lewat aplikasi lain</button>' : ''}
      <p class="share-sub">Atau pilih tujuan:</p>
      <div class="share-grid">
        ${targets(msg, url).map(t => `
          <a class="share-opt" href="${t.href}" target="_blank" rel="noopener noreferrer" data-id="${t.id}">
            <span class="share-dot" style="background:${t.color}">${t.mark}</span><small>${t.label}</small>
          </a>`).join('')}
        <button type="button" class="share-opt" data-act="ig">
          <span class="share-dot ig">IG</span><small>Instagram</small>
        </button>
        <button type="button" class="share-opt" data-act="copy-link">
          <span class="share-dot plain">\u29c9</span><small>Salin tautan</small>
        </button>
        <button type="button" class="share-opt" data-act="download">
          <span class="share-dot plain">\u2193</span><small>Unduh gambar</small>
        </button>
      </div>
      <p class="share-hint">Jika perangkat mendukung berbagi file, gunakan “Bagikan lewat aplikasi lain” untuk mengirim gambar. Tautan aplikasi sosial membuka halaman berbagi; lampirkan gambar yang diunduh jika ingin ikut membagikan kartu.</p>
    </div>`;
  const prev = root.querySelector('.share-preview');
  canvas.setAttribute('role', 'img');
  canvas.setAttribute('aria-label', 'Pratinjau kartu statistik mingguan');
  prev.appendChild(canvas);
  document.body.appendChild(root);
  document.body.style.overflow = 'hidden';

  const close = () => {
    root.remove();
    document.body.style.overflow = '';
    document.removeEventListener('keydown', onKey);
    openModal = null;
    if (opener && opener.focus) opener.focus();
  };
  const onKey = e => {
    if (e.key === 'Escape') { close(); return; }
    if (e.key !== 'Tab') return;
    const f = [...root.querySelectorAll('button, a[href]')].filter(el => !el.disabled);
    if (!f.length) return;
    const first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  };
  document.addEventListener('keydown', onKey);
  openModal = close;

  root.addEventListener('click', async e => {
    if (e.target === root || e.target.closest('.share-close')) { close(); return; }
    const b = e.target.closest('[data-act]');
    if (!b) {
      const link = e.target.closest('.share-opt[data-id]');
      if (!link) return;
      // Buka halaman berbagi yang dipilih dan siapkan gambar untuk dilampirkan.
      if (blob) {
        download(blob, 'laporan-suapin.png');
        toast('Kartu diunduh. Lampirkan gambar di aplikasi tujuan.', 'check');
      }
      return;
    }
    const act = b.dataset.act;
    if (act === 'native') {
      try {
        if (canNativeFile) await navigator.share({ files: [file], text: msg, url });
        else await navigator.share({ text: msg, url });
      } catch { /* user menutup menu bagikan */ }
    } else if (act === 'download' || act === 'ig') {
      if (blob) {
        download(blob, 'laporan-suapin.png');
        toast(act === 'ig' ? 'Gambar berhasil diunduh. Buka Instagram untuk mengunggahnya ke Story.' : 'Laporan berhasil diunduh!', 'check');
      } else toast('Gagal membuat gambar laporan.', 'check');
    } else if (act === 'copy-link') {
      toast((await copyText(url)) ? 'Tautan laporan berhasil disalin!' : 'Gagal menyalin tautan.', 'check');
    }
  });

  root.querySelector('.share-close').focus();
}
