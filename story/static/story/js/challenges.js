(() => {
    const content = document.getElementById('challenge-content');
    const feedback = document.getElementById('challenge-feedback');

    if (!content || !feedback) return;

    let busy = false;

    // Event di wadahnya tetap jalan setelah daftar kartu diganti.
    content.addEventListener('submit', async (event) => {
        const form = event.target.closest('.challenge-action-form');
        if (!form) return;

        event.preventDefault();

        if (busy) return;
        busy = true;

        const button = form.querySelector('button');
        const label = button.textContent;

        button.disabled = true;
        button.textContent = 'Memproses…';
        feedback.textContent = '';
        content.setAttribute('aria-busy', 'true');

        try {
            const response = await fetch(form.action, {
                method: 'POST',

                // Token CSRF ikut dikirim lewat isi form.
                body: new FormData(form),
                headers: {
                    Accept: 'application/json',
                },
                credentials: 'same-origin',
            });

            // klo sesi login habis, ikuti halaman login dari server.
            if (response.redirected) {
                window.location.assign(response.url);
                return;
            }

            if (!response.ok) {
                throw new Error('Aksi gagal');
            }

            const data = await response.json();
            // HTML udah dirender Django, tinggal ganti daftar yg tampil
            content.innerHTML = data.html;
            feedback.textContent = data.message;
        } catch (error) {
            feedback.textContent =
                'Status belum bisa dimuat. Refresh halaman untuk mengecek hasilnya sebelum mencoba lagi.';
        } finally {
            busy = false;
            content.removeAttribute('aria-busy');

            if (button.isConnected) {
                button.disabled = false;
                button.textContent = label;
            }
        }
    });
})();