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

---

### Modul Gamifikasi + XP + Level
**PIC: Muhammad Ziad Ayyash**

#### Alat dan cakupan penggunaan

Saya menggunakan **Claude - Sonnet 5.5 (Free Plan)** selama pengembangan modul ini untuk membantu merancang alur fitur, menghasilkan kode, memperbaiki error, menyusun pengujian, dan mempelajari implementasinya. Penggunaan AI mencakup logika backend dan frontend, bukan hanya penulisan komentar atau perapian kode.

Bantuan AI digunakan pada bagian berikut:

| Bagian | Bentuk bantuan AI |
| --- | --- |
| Models | Memberikan ide untuk membuat `UserBadge` untuk merepresentasikan _ownership_ suatu pengguna terhadap suatu `Badge`, menyarankan untuk menambahkan field data yang berkaitan dengan freeze streak pada `GameProfile`, serta menambah restriksi level pada `GameProfile` dan menambah constraints pada `UserBadge` |
| Views | Membantu menyusun _services_ yang dibutuhkan modul, serta membantu menyusun context yang dibutuhkan view streak dan level |
| Template | Membantu memberikan desain awal untuk halaman streak, level, dan form untuk badge |
| Form | - |
| Interaktivitas sisi klien | Membantu mengimplementasikan fitur filter, sort, dan delete pada halaman badge |
| Pengujian | Membantu menyusun skenario dan kode unit test untuk _service_ milik gamifikasi dan tampilan halaman |

#### Strategi penggunaan prompt

Prompt diberikan secara bertahap per fitur dengan menyertakan konteks proyek dan file. Untuk _bugfixing_, saya meminta AI untuk menjelaskan cara kerja bagian kode yang ia ubah, serta alasan mengapa menggunakan pendekatan tersebut.

Saya juga meminta tolong AI untuk meringkas dan menjelaskan fitur yang ditambahkan oleh anggota kelompok lain supaya bisa mengintegrasikan fitur yang mereka implementasi dengan fitur - fitur gamifikasi.

#### Keterbatasan AI dan perbaikan selama pengerjaan

Beberapa masalah yang ditemukan selama pengerjaan adalah:

1. **Desain tidak mempertimbangkan base.** Beberapa desain awal halaman memiliki berbagai macam ketidaksesuaian akibat AI menggunakan nama class yang konflik dengan CSS yang sudah disediakan base.
2. **Membuat suatu file besar monolitik.** Sejumlah desain html yang diberikan menyantumkan semua elemen di dalam satu file html daripada memisahkannya menjadi bagian - bagian seperti file css tersendiri dan partial html.
3. **Ketidaksesuaian implementasi minggu pada halaman streak.** Pada halaman streak, AI menampilkan aktivitas 7 hari kebelakang. Seharusnya menampilkan hari - hari dalam seminggu secara terurut.
4. **Memasukkan data yang tidak ada ke dalam context view.** Dalam membantu menulis context untuk suatu view, AI menggunakan fungsi, data, dan field yang tidak ada/belum diimplementasi.

Perbaikan tersebut dilakukan melalui perubahan file baik secara manual maupun dengan bantuan arahan AI. Saya tidak menganggap seluruh saran awal AI sudah benar tanpa perlu dicoba atau disesuaikan.

#### Validasi dan tanggung jawab

Kode diterapkan secara bertahap pada branch pengembangan, kemudian diperiksa melalui pengujian lokal, pengecekan tampilan browser, dan pemeriksaan pesan error. Perubahan dikirim melalui commit dan pull request untuk digabungkan dengan pekerjaan anggota kelompok lainnya.

Pengujian yang dilakukan membantu memeriksa perilaku fitur, tetapi tidak menjadi jaminan bahwa seluruh kemungkinan masalah telah tercakup. Keberhasilan tampilan di lingkungan lokal juga tidak langsung membuktikan bahwa konfigurasi dan data pada server deployment sudah sesuai.

Saya menggunakan penjelasan AI sebagai pendamping untuk mempelajari alur kode dan melakukan penyesuaian implementasi. Tanggung jawab atas kode, konten, dan perubahan yang saya sertakan dalam proyek tetap berada pada saya sebagai pengembang modul.

---

### Modul Challenge & Notifikasi (`challenge`)
**PIC: Annisa Saskya Aulia**

#### 1. Pemanfaatan AI dalam Proses Pengembangan

Selama mengerjakan modul Challenge pada aplikasi Suap.in, saya memanfaatkan ChatGPT dan Claude sebagai salah satu sumber bantuan dalam memahami permasalahan teknis dan mengembangkan fungsionalitas aplikasi. Penggunaannya tidak terbatas pada pembuatan potongan kode, tetapi juga mencakup diskusi mengenai pendekatan implementasi, pemeriksaan kesalahan, dan evaluasi hasil pengembangan.

Beberapa pekerjaan yang melibatkan bantuan AI antara lain:

- **Pengembangan profil pengguna:** Mendiskusikan cara menggabungkan informasi identitas pengguna dengan data perkembangan Challenge, seperti avatar, bio, XP, level, statistik pemindaian, dan pencapaian badge.
- **Sistem misi dan pencapaian:** Mengembangkan mekanisme misi harian, pencatatan aktivitas, perhitungan progres, serta pemberian penghargaan berdasarkan aktivitas yang dilakukan pengguna.
- **Sistem peringkat:** Membantu memahami pengolahan data XP dan penyusunan leaderboard, termasuk pencatatan perubahan peringkat pengguna dalam periode tertentu.
- **Pengelolaan notifikasi:** Mengembangkan mekanisme penyampaian informasi kepada pengguna, misalnya ketika terdapat misi baru, perubahan posisi ranking, pencapaian badge, maupun pembaruan aktivitas lainnya.
- **Penyusunan laporan:** Mendiskusikan pengolahan data aktivitas menjadi laporan mingguan, menampilkan statistik dan grafik, serta menyusun riwayat laporan berdasarkan periode yang telah ditentukan.
- **Pengembangan tampilan aplikasi:** Memanfaatkan AI untuk membantu menulis dan menyesuaikan komponen HTML, CSS, dan JavaScript agar interaksi pada halaman Challenge dapat berjalan sesuai rancangan.
- **Pemeriksaan kualitas kode:** Meminta bantuan dalam menyusun pengujian, membaca traceback, memahami perilaku fungsi, dan menemukan kemungkinan masalah pada hubungan antarmodul.

#### 2. Cara AI Digunakan Selama Pengerjaan

Penggunaan ChatGPT dilakukan dengan pendekatan diskusi dua arah. Saya terlebih dahulu menjelaskan fitur yang ingin dibuat atau kendala yang sedang dihadapi, kemudian memberikan informasi pendukung seperti struktur folder, isi file terkait, potongan kode, maupun hasil yang muncul ketika aplikasi dijalankan.

Untuk perubahan yang melibatkan beberapa file, saya meminta penjelasan mengenai hubungan antara model, view, URL, template, dan JavaScript yang terlibat. Hal ini membantu saya memahami dampak suatu perubahan sebelum menerapkannya.

Saya juga menggunakan AI untuk membandingkan beberapa alternatif penyelesaian masalah. Apabila jawaban yang diberikan belum sesuai dengan struktur proyek, saya memberikan konteks tambahan dan meminta pendekatan lain yang lebih cocok dengan implementasi Suap.in.

Dalam beberapa kasus, saya meminta perubahan dilakukan secara spesifik pada modul Challenge. Hal ini penting karena proyek dikembangkan secara berkelompok dan setiap anggota memiliki bagian pengerjaan masing-masing. Oleh sebab itu, saya perlu memastikan perubahan tidak mengganggu pekerjaan anggota lain.

#### 3. Contoh Permasalahan yang Melibatkan Bantuan AI

Selama proses pengembangan, terdapat beberapa situasi ketika solusi awal belum memberikan hasil yang diharapkan. Beberapa di antaranya adalah:

**a. Halaman Challenge tidak dapat ditampilkan**
Setelah melakukan perubahan pada JavaScript, halaman Challenge sempat hanya menampilkan halaman kosong. Pemeriksaan melalui browser Console menunjukkan adanya masalah pada proses import fungsi `markGone` dari `state.js` oleh `notifikasi.js`. Saya menggunakan bantuan ChatGPT untuk memahami penyebab error tersebut, kemudian memeriksa kembali fungsi yang tersedia dan menyesuaikan pemanggilannya.

**b. Riwayat migration tidak sesuai dengan kondisi database**
Ketika menambahkan perubahan pada model Challenge, Django sempat mengalami konflik karena terdapat tabel yang sudah tersedia di database tetapi belum tercatat sesuai dengan nama migration yang digunakan. Saya meminta bantuan untuk memahami hubungan antara file migration dan catatan migration pada database. Setelah itu, saya memeriksa hasil `showmigrations`, menyesuaikan nama file, dan memperbaiki dependency antarmigration.

**c. Kesalahan dalam pembentukan notifikasi**
Pada salah satu proses pengembangan notifikasi, aplikasi menghasilkan `NameError` karena variabel `since` belum didefinisikan ketika digunakan dalam fungsi `build_notifications`. ChatGPT membantu menelusuri bagian kode yang berkaitan dengan error tersebut. Saya kemudian menyesuaikan logika fungsi berdasarkan konteks program yang sebenarnya.

**d. Hasil pengujian reward belum sesuai**
Pengujian terhadap sistem badge menunjukkan bahwa beberapa pencapaian belum tercatat sebagaimana mestinya. Selain itu, terdapat pemanggilan fungsi `ensure_badges` yang belum sesuai dengan fungsi yang tersedia pada modul gamifikasi. Saya menggunakan AI untuk membantu menganalisis hubungan antara proses scan, pemberian XP, dan pencatatan badge. Hasil analisis tersebut kemudian menjadi dasar untuk pemeriksaan dan perbaikan kode.

**e. Ketidakkonsistenan periode laporan**
Dalam pengembangan laporan mingguan, ditemukan bahwa pembagian periode laporan perlu diselaraskan dengan periode leaderboard. Saya mendiskusikan logika perhitungan tanggal dengan ChatGPT agar laporan menggunakan rentang minggu yang tetap, bukan sekadar menghitung tujuh hari ke belakang dari tanggal pengguna membuka halaman.

Permasalahan-permasalahan tersebut memperlihatkan bahwa jawaban AI tidak selalu dapat langsung diterapkan. Diperlukan pemeriksaan tambahan terhadap kode dan hasil eksekusi untuk memastikan solusi yang digunakan benar-benar menyelesaikan masalah.

#### 4. Pemeriksaan Hasil dan Evaluasi

Setiap perubahan yang dibantu oleh AI tetap melalui proses pemeriksaan sebelum digunakan dalam proyek. Saya menjalankan aplikasi secara lokal untuk melihat apakah fitur bekerja sebagaimana mestinya, memeriksa tampilan melalui browser, dan menggunakan perintah pengujian Django untuk mengevaluasi perilaku kode.

Pengujian juga membantu menemukan masalah yang tidak terlihat hanya dari pemeriksaan kode, misalnya ketika data badge belum terbentuk, progres belum diperbarui, atau hasil laporan tidak sesuai dengan periode yang diharapkan.

Apabila ditemukan kegagalan, saya tidak langsung menganggap hasil AI sebagai solusi akhir. Saya memeriksa kembali bagian yang bermasalah, memberikan hasil pengujian kepada AI sebagai konteks tambahan, lalu melakukan penyesuaian berdasarkan kondisi proyek.

#### 5. Pernyataan Tanggung Jawab

ChatGPT dan Claude digunakan sebagai sarana pendukung selama proses belajar dan pengembangan modul Challenge. Penggunaan AI membantu mempercepat pencarian solusi teknis sekaligus memberikan penjelasan mengenai bagian kode yang belum saya pahami.

Meskipun demikian, keputusan mengenai penggunaan suatu solusi, penyesuaian kode terhadap kebutuhan aplikasi, dan pemeriksaan hasil implementasi tetap dilakukan oleh saya. Saya memahami bahwa kode yang dihasilkan AI dapat mengandung kesalahan atau tidak sesuai dengan struktur proyek yang sedang dikerjakan.

Dengan demikian, saya bertanggung jawab atas perubahan dan kontribusi yang saya berikan pada modul Challenge dalam proyek Suap.in.

---

PBP C — Fakultas Ilmu Komputer, Universitas Indonesia — Semester Gasal 2026/2027

