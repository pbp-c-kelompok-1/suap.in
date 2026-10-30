# Suap.in: Foto makananmu, jaga bumiku.

Platform web gamifikasi tracking carbon footprint makanan harian berbasis AI — dirancang khusus untuk makanan Indonesia.

## 👥 Anggota Kelompok

| Syahid Arkan Fashihurrohman | 2506632936 | [@syahidarkan](https://github.com/syahidarkan) |
| Muhammad Iqbal | 2506657075 | [@labqimm](https://github.com/labqimm) |
| Nasywa Namira Suhendro | 2506532196 | [@nasywanamira](https://github.com/nasywanamira) |
| Annisa Saskya Aulia | 2506537915 | [@annisasaskya3-art](https://github.com/annisasaskya3-art) |
| Muhammad Ziad Ayyash | 2506594364 | [@ziad-ayyash](https://github.com/ziad-ayyash) |

## 📖 Deskripsi Aplikasi

### Masalah

Sektor pangan menyumbang 26% emisi karbon global, lebih dari seluruh transportasi darat yang digabung. Di Indonesia, tidak ada cara mudah bagi masyarakat untuk mengetahui dampak lingkungan dari pilihan makan mereka sehari-hari. Semua food carbon calculator yang ada itu adalah berbasis menu makanan Barat, butuh input manual yang ribet, dan tidak ada yang bikin orang mau balik lagi.

Hasilnya yakni orang tidak pernah berubah, karena tidak ada yang memberi tahu mereka secara personal, menarik, dan konsisten.

### Solusi

Suap.in menampung kebiasaan yang sudah ada: orang makan 3x sehari, dan foto makanan sebelum dimakan sudah jadi kebiasaan Gen Z. Tinggal kasih memberikan dampak dari kebiasaan yang sudah dilakukan tersebut.

1. User foto makanan
2. AI deteksi semua item dan hitung emisi karbon
3. data masuk ke sistem gamifikasi berlapis yang bikin orang kompetitif, konsisten, dan ketagihan buka app setiap hari
4. Kesadaran masyarakat terhadap Efek Karbon yang dihasilkan oleh makanan tertentu meningkat
5. Pengurangan Emisi Karbon dari sektor Pangan

### Siapa Penggunanya?

Mahasiswa Indonesia usia 18–25 tahun yang makan di luar setiap hari dan mulai sadar soal sustainability tapi tidak tahu mulai dari mana dan tidak punya waktu untuk riset sendiri.

### Kenapa Beda dari yang Lain? (Value Prepositions)

Suap.in adalah satu-satunya platform yang menggabungkan:

1. Streak System — foto minimal 1 makanan/hari, streak terjaga. Skip = streak hilang (model Duolingo). Ada streak freeze maksimal 2x/minggu dari reward harian.
2. Social Competition — leaderboard mingguan 3 level (teman, kampus, nasional) + 1v1 Friend Challenge + Campus War antar universitas.
3. Avatar Consequences — avatar makhluk hidup yang kondisinya mencerminkan pilihan makan user. Visible di profil publik, ada social pressure untuk jaga kondisinya.
4. Story Progression — setiap foto = XP → naik level → unlock episode komik digital tentang perjalanan makanan dari sumber ke piring.
5. AI Food Scanner — satu-satunya scanner yang pakai model (EfficientNet fine-tuned khusus makanan Indonesia) dengan 4 layer fallback system. Tidak bergantung satu API, tidak ada biaya, dan makin akurat seiring pakai karena database karbon dikembangkan dari data FAO + publikasi akademik Indonesia.

Kombinasi 4 psychological hook ini dan 1 fitur Machine Learning yang belum pernah diterapkan di platform sustainability manapun.

## 🧩 Daftar Modul

### 1. Auth + Profil + Avatar (`authentication`)
PIC: Syahid Arkan Fashihurrohman
Register, login, halaman profil publik, avatar system dengan evolution path (Benih → Tunas → Pohon Kecil → Pohon Besar → Hutan), kondisi avatar berubah real-time berdasarkan streak dan carbon score.
- Landing Page — halaman utama guest, value proposition dan CTA daftar/masuk
- Register Page — form pendaftaran akun baru
- Login Page — form masuk akun
- Profil Publik — halaman profil user dengan avatar, stats, dan badges
- Avatar Page — tampilan kondisi avatar dan evolution path (Benih → Hutan)

### 2. FoodScan AI + Machine Learning (`scanner`)
PIC: Syahid Arkan Fashihurrohman
Upload foto makanan, 4-layer AI detection (EfficientNet → Groq Llama 3.2 Vision → Gemini 1.5 Flash → manual input), kalkulasi emisi CO₂ per item, daily log, daily carbon budget tracker dengan progress bar real-time.
- Scan Page — kamera atau upload foto makanan untuk dideteksi AI
- Hasil Scan Page — breakdown item terdeteksi, emisi CO₂ per item, XP didapat, saran alternatif
- Daily Log Page — riwayat semua scan hari ini
- Carbon Budget Page — progress bar karbon harian real-time

### 3. Gamifikasi + XP + Level
PIC: Muhammad Ziad Ayyash
Streak system dengan freeze mechanic, XP accumulation, sistem level 50 tier (Pemula Sadar → Pejuang Hijau → Guardian Bumi → Legenda Lestari), badge.
- Dashboard — home utama setelah login, ringkasan streak, budget, dan challenge
- Streak Page — status streak aktif, streak freeze, dan milestone counter
- Level & XP Page — progress XP, tier level saat ini, dan target tier berikutnya
- Badges Page — koleksi lencana yang sudah dan belum di-unlock

### 4. Leaderboard + Campus War (`social`)
PIC: Muhammad Iqbal
Friend system, leaderboard mingguan 3 level (teman/kampus/nasional), Campus War (kompetisi carbon footprint agregat antar universitas bulanan).
- Leaderboard Page — ranking mingguan dengan tab teman, kampus, dan nasional
- Campus War Page — kompetisi carbon footprint agregat antar universitas bulanan
- Friends Page — daftar teman dan fitur tambah teman

### 5. Challenge + Weekly Report (`challenge`)
PIC: Annisa Saskya Aulia
Generasi daily challenge otomatis (3 challenge/hari berdasarkan kebiasaan user), weekly carbon report (recap CO₂, perbandingan minggu lalu, proyeksi tahunan, ranking), sistem notifikasi, carbon budget integration.
- Daily Challenge Page — 3 challenge harian otomatis berdasarkan kebiasaan user
- Weekly Report Page — recap total CO₂, perbandingan minggu lalu, proyeksi tahunan, ranking
- Notifikasi Page — pusat notifikasi streak, challenge, dan leaderboard

### 6. Story Progression + 1v1 Challenge (`story`)
PIC: Nasywa Namira Suhendro
story progression (unlock komik digital per level range), milestone rewards, friend system, 1v1 Friend Challenge, share stats ke Instagram Story.
- Story Page — episode komik digital yang unlock per range level
- Milestone Rewards Page — hadiah dan pencapaian per milestone streak/level
- 1v1 Challenge Page — tantangan langsung antar dua user
- Share Stats Page — preview card weekly stats untuk dibagikan ke Instagram Story

## 🔧 CRUD per Modul

### authentication (PIC: Syahid Arkan Fashihurrohman)

**User & Profile**
- Create: Register akun baru
- Read: Lihat profil sendiri/publik
- Update: Edit bio, foto profil
- Delete: Hapus akun

**Avatar**
- Create: Inisialisasi avatar saat register
- Read: Lihat kondisi & evolution path avatar
- Update: Update kondisi avatar otomatis berbasis streak dan carbon score

### scanner (PIC: Syahid Arkan Fashihurrohman)

**FoodLog**
- Create: Buat entry dari hasil scan foto
- Read: Lihat riwayat daily log dan detail hasil scan
- Update: Koreksi manual item yang salah terdeteksi
- Delete: Hapus entry log yang salah atau duplikat

**CarbonBudget**
- Create: Inisialisasi budget harian
- Read: Lihat progress carbon budget real-time
- Update: Update sisa budget tiap scan baru

### gamification (PIC: Muhammad Ziad Ayyash)

**Streak**
- Create: Inisialisasi streak saat scan pertama
- Read: Lihat status streak dan milestone counter
- Update: Increment/reset streak, klaim streak freeze

**XP & Level**
- Create: Buat XP transaction tiap scan
- Read: Lihat progress XP dan tier level
- Update: Tambah XP, unlock tier baru

**Badge**
- Create: Unlock badge otomatis saat milestone tercapai
- Read: Lihat koleksi badge (locked/unlocked)

### social (PIC: Muhammad Iqbal)

**Friendship**
- Create: Kirim friend request
- Read: Lihat daftar teman
- Update: Terima/tolak friend request
- Delete: Unfriend/hapus pertemanan

**Leaderboard**
- Create: Submit skor mingguan otomatis
- Read: Lihat ranking teman/kampus/nasional

**CampusWar**
- Read: Lihat status kompetisi antar kampus
- Update: Update skor agregat kampus otomatis

### challenge (PIC: Annisa Saskya Aulia)

**DailyChallenge**
- Create: Generate 3 challenge harian otomatis
- Read: Lihat daftar challenge harian
- Update: Tandai challenge selesai

**WeeklyReport**
- Create: Buat laporan mingguan otomatis
- Read: Lihat recap CO₂ dan proyeksi tahunan

**Notification**
- Create: Buat notifikasi baru dari sistem
- Read: Lihat pusat notifikasi
- Update: Tandai sudah dibaca
- Delete: Hapus notifikasi lama

### story (PIC: Nasywa Namira Suhendro)

**Story/Comic**
- Create: Unlock episode baru saat naik level otomatis
- Read: Lihat daftar dan isi episode yang ter-unlock

**MilestoneReward**
- Create: Buat reward saat milestone tercapai otomatis
- Read: Lihat daftar reward
- Update: Klaim reward

**FriendChallenge (1v1)**
- Create: Buat tantangan 1v1 ke teman
- Read: Lihat status dan hasil tantangan
- Update: Update progress tantangan
- Delete: Batalkan tantangan yang belum diterima


## 🌐 Public API

- Groq Llama 3.2 Vision — Food detection Layer 2, identifikasi item makanan dari foto. [Docs](https://console.groq.com/docs/vision)
- Google Gemini 1.5 Flash — Food detection Layer 3, fallback jika Groq rate limit. [Docs](https://ai.google.dev/gemini-api/docs)
- Open-Meteo — Data cuaca lokal untuk konteks makanan seasonal dan rekomendasi. [Docs](https://open-meteo.com/en/docs)
- Open Food Facts — Database produk makanan kemasan, lookup nama brand dari foto bungkus. [Docs](https://world.openfoodfacts.org/data)
- **Open Food Facts API** — Sumber 50 initial data produk makanan kemasan (nama produk, kategori, berat). Data diambil via `https://world.openfoodfacts.org/cgi/search.pl?action=process&tagtype_0=categories&tag_contains_0=contains&tag_0=indonesian-food&json=1` dan diseed ke database saat pertama deploy. [Docs](https://world.openfoodfacts.org/data)

## 👤 Peran Pengguna

- Guest — Pengunjung yang belum daftar. Bisa akses landing page, demo scan (tanpa simpan data), dan lihat leaderboard publik.
- Member — Mahasiswa/pengguna terdaftar. Akses semua fitur: scan makanan, streak, leaderboard, challenge harian, avatar, dan weekly report.
- Admin — Pengelola platform. Kelola challenge harian, moderasi konten, pantau anomali data, dan dashboard agregat carbon footprint.

## 🚀 Deployment

- PWS: (https://syahid-arkan-suapin.pws.cs.ui.ac.id)
- Figma Design: (https://www.figma.com/design/mszscHVDXDGjBYLDDYCKmH/Suap.in-Lo-Fi?node-id=0-1&p=f&t=GTGm14cmdJaEurVJ-0)

## 🗂️ Struktur Proyek

```
suap-in/
├── suap_in/          # Django project (settings, urls, wsgi)
├── authentication/   # Modul auth + profil + avatar (PIC: Syahid Arkan)
├── scanner/          # Modul FoodScan AI + carbon log (PIC: Syahid Arkan)
├── gamification/     # Modul streak + level & XP + badges (PIC: Muhammad Ziad Ayyash)
├── social/           # Modul leaderboard + campus war + friends (PIC: Muhammad Iqbal)
├── challenge/        # Modul daily challenge + weekly report + notifikasi (PIC: Annisa Saskya Aulia)
├── story/            # Modul komik digital + milestone rewards + 1v1 challenge (PIC: Nasywa Namira Suhendro)
├── templates/        # Shared HTML templates (base.html, navbar, footer)
├── static/           # CSS, JS, images
├── .github/
│   └── workflows/
│       ├── ci.yml      # CI: Django system checks & automated test suite
│       └── deploy.yml  # CD: Auto-deploy ke PWS
├── requirements.txt
├── manage.py
└── README.md
```

## ⚙️ Tech Stack

- Backend: Django 5.0
- Database: PostgreSQL (PWS, schema `tugas_kelompok`)
- AI Layer 1: TensorFlow + EfficientNet (fine-tuned)
- AI Layer 2: Groq Llama 3.2 Vision
- AI Layer 3: Gemini 1.5 Flash
- Frontend: Django Templates + CSS + Vanilla JS
- Deployment: PWS (Pacil Web Service)
- Version Control & CI/CD: GitHub Organization (`pbp-c-kelompok-1`) + GitHub Actions

Total biaya infrastruktur: Rp 0

## 🤖 Deklarasi Penggunaan AI

Dalam pengembangan proyek tengah semester **Suap.in**, kelompok kami memanfaatkan alat bantu kecerdasan buatan (*Generative AI / Large Language Models*) seperti **Google Gemini**, **Claude**, dan **ChatGPT** dengan ketentuan dan rincian penggunaan sebagai berikut:

1. **Perancangan & Brainstorming**: Digunakan untuk eksplorasi ide arsitektur gamifikasi makanan Indonesia, skenario alur pengguna (*user flow*), serta perancangan relasi antar-model.
2. **Pengembangan & Debugging**: Digunakan sebagai asisten pemrograman (*pair programming*) untuk membantu penulisan kode *boilerplate*, perbaikan pesan error, penanganan *edge cases*, dan optimasi kueri Django ORM.
3. **Pengujian (*Automated Testing*)**: Digunakan untuk membantu menyusun skenario *unit test* dan *integration test* guna memverifikasi keandalan fungsionalitas CRUD, alur notifikasi, dan integrasi antar-modul.
4. **Dokumentasi & Konsultasi Teknis**: Digunakan untuk merapikan draf dokumentasi teknis dan referensi API publik.

> **Pernyataan Integritas**: Seluruh baris kode, arsitektur, dan logika bisnis yang dihasilkan atau disarankan oleh kecerdasan buatan telah ditinjau, dipahami, dimodifikasi, disesuaikan dengan kebutuhan proyek PBP Gasal 2026/2027, serta diuji secara langsung oleh seluruh anggota tim. Kelompok kami bertanggung jawab penuh atas substansi, orisinalitas, dan fungsionalitas aplikasi yang diserahkan.


### Modul Story Progression + 1v1 Challenge (`story`)
**PIC: Nasywa Namira Suhendro**

#### Alat dan cakupan penggunaan

Saya menggunakan **ChatGPT** selama pengembangan modul ini untuk membantu merancang alur fitur, menghasilkan kode, memperbaiki error, menyusun pengujian, dan mempelajari implementasinya. Penggunaan AI mencakup logika backend dan frontend, bukan hanya penulisan komentar atau perapian kode.

Bantuan AI digunakan pada bagian berikut:

| Bagian | Bentuk bantuan AI |
| --- | --- |
| Story/Comic | Membantu menyusun model, URL, view, dan template untuk daftar serta pembaca komik; pencarian dan penyaringan bab; pembatasan akses berdasarkan level; serta pengelolaan bab dan halaman oleh pengguna staff. |
| Konten cerita | Membantu menyusun judul, narasi, dialog, dan ilustrasi cerita yang mengikuti perjalanan makanan serta tema jejak karbon. |
| Data awal komik | Membantu menyiapkan data JSON dan data migration untuk memasukkan konten awal ke database. |
| Milestone Rewards | Membantu menyusun syarat milestone level dan streak, pencatatan reward, tampilan progres, serta proses klaim dan pemberian XP dengan pencegahan klaim berulang. |
| Tantangan 1v1 | Membantu menyusun alur pembuatan, penerimaan, pembatalan, dan pembaruan tantangan; penentuan periode pertandingan; perhitungan skor berdasarkan catatan makanan; serta penyimpanan hasil akhir. |
| Antarmuka dan AJAX | Membantu menulis HTML, CSS, dan JavaScript untuk tampilan modul serta pembaruan bagian halaman melalui fetch dan respons JSON. |
| Pengujian | Membantu menyusun skenario dan kode unit test untuk akses pengguna, pembatasan level, klaim reward, perubahan status tantangan, serta perhitungan hasil pertandingan. |
| Penyesuaian visual | Membantu memasang aset maskot pada beberapa tampilan aplikasi dan menyusun ulang halaman Story menjadi layer desain yang dapat diedit di Figma berdasarkan screenshot. |

#### Strategi penggunaan prompt

Prompt diberikan secara bertahap per fitur dengan menyertakan konteks proyek, potongan kode, struktur file, screenshot tampilan, atau pesan error yang sedang terjadi. Saya meminta kode yang mudah dibaca, penjelasan lokasi perubahan file, langkah implementasi yang berurutan, dan komentar yang membantu menjelaskan fungsi kode.

Saya juga meminta agar pendekatan implementasi disesuaikan dengan pola yang dipelajari dalam tutorial PBP. Penjelasan tambahan diminta ketika terdapat istilah, alur, atau bagian kode yang belum saya pahami.

Ketika hasil implementasi belum sesuai, saya mengirimkan kembali hasil pengujian, screenshot, atau pesan error sebagai konteks untuk memperbaiki jawaban sebelumnya. Dengan demikian, implementasi berkembang melalui beberapa iterasi.

#### Keterbatasan AI dan perbaikan selama pengerjaan

Saran AI tidak selalu langsung sesuai dengan kondisi repository maupun lingkungan deployment. Beberapa masalah yang ditemukan selama pengerjaan adalah:

1. **Perbedaan database lokal dan deployment.** Halaman Story di server sempat tidak menampilkan bab meskipun kode dan template sudah tersedia. Dari proses pemeriksaan, pengiriman kode saja belum cukup untuk menyediakan isi database. Perbaikannya dilakukan dengan menambahkan data migration untuk konten awal komik, yang perlu dijalankan pada database deployment.

2. **Ketidaksesuaian nama migration.** Salah satu instruksi menggunakan nama file migration yang tidak sesuai dengan file dalam repository. Nama file diperiksa kembali dan instruksi disesuaikan dengan struktur migration yang sebenarnya.

3. **Ketidaksesuaian import JavaScript.** Setelah perubahan fungsi pemasangan maskot, halaman sempat kosong karena `notifikasi.js` masih mengimpor `avatarSvg`, sementara fungsi tersebut sudah tidak diekspor dari `mascot.js`. Pesan error diperiksa melalui browser Console, kemudian import dan pemanggilan fungsi disesuaikan menjadi `mountMascot`.

4. **Pengaruh data awal terhadap pengujian.** Penambahan konten melalui migration memengaruhi pengujian yang mengasumsikan database cerita kosong. Setup pada pengujian terkait disesuaikan dengan membersihkan data cerita di database pengujian sebelum membuat data uji.

Perbaikan tersebut dilakukan melalui perubahan file secara manual dengan bantuan arahan AI. Saya tidak menganggap seluruh saran awal AI sudah benar tanpa perlu dicoba atau disesuaikan.

#### Validasi dan tanggung jawab

Kode diterapkan secara bertahap pada branch pengembangan, kemudian diperiksa melalui pengujian lokal, pengecekan tampilan browser, dan pemeriksaan pesan error. Perubahan dikirim melalui commit dan pull request untuk digabungkan dengan pekerjaan anggota kelompok lainnya.

Pengujian yang dilakukan membantu memeriksa perilaku fitur, tetapi tidak menjadi jaminan bahwa seluruh kemungkinan masalah telah tercakup. Keberhasilan tampilan di lingkungan lokal juga tidak langsung membuktikan bahwa konfigurasi dan data pada server deployment sudah sesuai.

Saya menggunakan penjelasan AI sebagai pendamping untuk mempelajari alur kode dan melakukan penyesuaian implementasi. Tanggung jawab atas kode, konten, dan perubahan yang saya sertakan dalam proyek tetap berada pada saya sebagai pengembang modul.

PBP C — Fasilkom UI — Semester Gasal 2026/2027