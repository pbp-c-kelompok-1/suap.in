(() => {
    const content = document.getElementById('reward-content');
    const feedback = document.getElementById('reward-feedback');

    if (!content || !feedback) return;

    let busy = false;

    // Pasang event di wadahnya supaya tetap jalan setelah kartu diganti
    content.addEventListener('submit', async (event) => {
        const form = event.target.closest('.reward-claim-form');
        if (!form) return;

        event.preventDefault();

        // Tunggu request sebelumnya selesai dulu
        if (busy) return;
        busy = true;

        const button = form.querySelector('button');
        const oldLabel = button.textContent;

        button.disabled = true;
        button.textContent = 'Mengklaim…';
        feedback.textContent = '';
        content.setAttribute('aria-busy', 'true');

        try {
            const response = await fetch(form.action, {
                method: 'POST',

                // FormData ikut membawa csrfmiddlewaretoken dari form
                body: new FormData(form),
                headers: {
                    Accept: 'application/json',
                },
                credentials: 'same-origin',
            });

            if (!response.ok || response.redirected) {
                throw new Error('Klaim gagal');
            }

            const data = await response.json();

            // HTML berasal dari template Django, termasuk tombol dan CSRF terbaru
            content.innerHTML = data.html;
            feedback.textContent = data.message;
        } catch (error) {
            // Request bisa aja udah diproses tapi responsnya gagal diterima
            // Klaim ulang tetap dicek server supaya XP nggak bertambah dua kali
            feedback.textContent =
                'Status klaim belum bisa dimuat. Coba lagi atau refresh halaman untuk mengeceknya.';
        } finally {
            busy = false;
            content.removeAttribute('aria-busy');

            // klo kartunya blm diganti, aktifkan lg tombol yg lama
            if (button.isConnected) {
                button.disabled = false;
                button.textContent = oldLabel;
            }
        }
    });
})();