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

### 6. Social + Story (`gamification`)
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
├── authentication/   # Modul auth + profil + avatar (PIC: Ziad)
├── scanner/          # Modul FoodScan AI + carbon log (PIC: Nami)
├── gamification/     # Modul gamifikasi + XP + story (PIC: Acan)
├── social/           # Modul social + leaderboard (PIC: Iqbal)
├── challenge/        # Modul challenge + weekly report (PIC: Nisa)
├── templates/        # Shared HTML templates (base.html, navbar, footer)
├── static/           # CSS, JS, images
├── .github/
│   └── workflows/
│       └── deploy.yml  # CI/CD auto-deploy ke PWS
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
- Frontend: Django Templates + Tailwind CSS + Vanilla JS
- Deployment: PWS (Pacil Web Service)
- Version Control: GitHub Organization (`pbp-c-kelompok-1`)

Total biaya infrastruktur: Rp 0

PBP C — Fasilkom UI — Semester Gasal 2026/2027