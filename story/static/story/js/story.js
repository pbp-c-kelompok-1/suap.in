(() => {
  'use strict';
  // Pakai ulang Tunas dari template maskot yang udah ada di project.
  const mascot = document.getElementById('mascot-tpl');
  if (mascot) document.querySelectorAll('[data-story-mascot]').forEach(slot => slot.appendChild(mascot.content.cloneNode(true)));

  const form = document.getElementById('story-filters');
  if (form) {
    const grid = document.getElementById('story-grid');
    const status = document.getElementById('story-results');
    const error = document.getElementById('story-filter-error');
    let timer, controller;
    async function refresh(event) {
      if (event) event.preventDefault();
      // Batalkan pencarian sebelumnya biar hasil ketikan lama nggak muncul belakangan.
      if (controller) controller.abort();
      controller = new AbortController();
      const request = controller;
      const url = new URL(form.action || window.location.href);
      url.search = new URLSearchParams(new FormData(form)).toString();
      grid.setAttribute('aria-busy', 'true');
      error.hidden = true;
      try {
        const response = await fetch(url, {headers: {'Accept': 'application/json'}, signal: request.signal});
        if (response.redirected) { window.location.assign(response.url); return; }
        if (!response.ok) throw new Error('Filter gagal');
        const data = await response.json();
        if (request !== controller) return;
        // Django udah merender dan meng-escape isi kartunya. Tinggal ganti daftar yang tampil.
        grid.innerHTML = data.html;
        status.textContent = `${data.count} bab ditemukan`;
        history.replaceState(null, '', url);
      } catch (exception) {
        if (exception.name !== 'AbortError') error.hidden = false;
      } finally {
        if (request === controller) grid.removeAttribute('aria-busy');
      }
    }
    form.addEventListener('submit', event => { clearTimeout(timer); refresh(event); });
    // Tunggu 300 ms setelah ketikan terakhir sebelum mengirim pencarian.
    form.querySelector('[name=q]').addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(refresh, 300); });
    form.querySelector('[name=status]').addEventListener('change', () => { clearTimeout(timer); refresh(); });
  }
  // Panah keyboard bisa buat pindah halaman, kecuali user lagi mengetik di input.
  if (document.getElementById('reader')) document.addEventListener('keydown', event => {
    if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey || event.target.closest('input,textarea,select,[contenteditable]')) return;
    const target = event.key === 'ArrowRight' ? 'story-next' : event.key === 'ArrowLeft' ? 'story-prev' : null;
    const link = target && document.getElementById(target);
    if (link) { event.preventDefault(); link.click(); }
  });
})();
