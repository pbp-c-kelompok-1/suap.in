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

### 2. FoodScan AI + Machine Learning (`scanner`)
PIC: Syahid Arkan Fashihurrohman
Upload foto makanan, 4-layer AI detection (EfficientNet → Groq Llama 3.2 Vision → Gemini 1.5 Flash → manual input), kalkulasi emisi CO₂ per item, daily log, daily carbon budget tracker dengan progress bar real-time.

### 3. Gamifikasi + XP + Level + Story (`gamification`)
PIC: Muhammad Ziad Ayyash
Streak system dengan freeze mechanic, XP accumulation, sistem level 50 tier (Pemula Sadar → Pejuang Hijau → Guardian Bumi → Legenda Lestari), badge, story progression (unlock komik digital per level range), milestone rewards.

### 4. Social + Leaderboard + Campus War (`social`)
PIC: Muhammad Iqbal
Friend system, leaderboard mingguan 3 level (teman/kampus/nasional), 1v1 Friend Challenge, Campus War (kompetisi carbon footprint agregat antar universitas bulanan), share stats ke Instagram Story.

### 5. Challenge + Weekly Report (`challenge`)
PIC: Annisa Saskya Aulia
Generasi daily challenge otomatis (3 challenge/hari berdasarkan kebiasaan user), weekly carbon report (recap CO₂, perbandingan minggu lalu, proyeksi tahunan, ranking), sistem notifikasi, carbon budget integration.

## 🌐 Public API

- Groq Llama 3.2 Vision — Food detection Layer 2, identifikasi item makanan dari foto. [Docs](https://console.groq.com/docs/vision)
- Google Gemini 1.5 Flash — Food detection Layer 3, fallback jika Groq rate limit. [Docs](https://ai.google.dev/gemini-api/docs)
- Open-Meteo — Data cuaca lokal untuk konteks makanan seasonal dan rekomendasi. [Docs](https://open-meteo.com/en/docs)
- Open Food Facts — Database produk makanan kemasan, lookup nama brand dari foto bungkus. [Docs](https://world.openfoodfacts.org/data)

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