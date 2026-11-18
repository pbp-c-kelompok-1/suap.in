"""
MODELS modul Social = "cetakan tabel" di database.

Setiap class di bawah = 1 tabel. Setiap atribut `models.XxxField` = 1 kolom.
Setelah mengubah file ini, jalankan:
    python manage.py makemigrations social   -> Django membuat "resep" perubahan tabel
    python manage.py migrate                 -> resep itu dijalankan ke database

Ringkasan tabel:
    University        : daftar kampus (UI, ITB, ...)
    CampusMembership  : user X kuliah di kampus Y (1 user = 1 kampus)
    Canteen           : kantin + koordinat GPS (untuk peta Community)
    CommunityPost     : foto makanan yang dibagikan ke peta Community
    PostReport        : laporan user terhadap post yang tidak pantas
    Friendship        : hubungan pertemanan antara 2 user
"""
from django.db import models
from django.contrib.auth.models import User  # tabel user bawaan Django (username, password, dll.)


class University(models.Model):
    """Satu kampus. Dipakai tab "Kampus" di leaderboard dan halaman Campus War."""

    # unique=True -> tidak boleh ada 2 kampus dengan nama yang sama (dicek oleh database)
    name = models.CharField(max_length=150, unique=True)        # contoh: "Universitas Indonesia"
    short_name = models.CharField(max_length=20, unique=True)   # contoh: "UI"
    # blank=True -> boleh dikosongkan di form/admin
    city = models.CharField(max_length=100, blank=True)         # contoh: "Depok"

    def __str__(self):
        # Teks yang muncul kalau objek ini di-print / ditampilkan di admin & dropdown.
        return self.short_name

    class Meta:
        # Urutan default setiap kali University.objects.all() dipanggil: A-Z berdasarkan short_name.
        ordering = ['short_name']
        # Nama jamak di halaman admin (default Django "Universitys" -> salah eja).
        verbose_name_plural = 'Universities'


class CampusMembership(models.Model):
    """Menyimpan "user ini kuliah di kampus mana".

    OneToOneField -> 1 user hanya boleh punya 1 baris (1 kampus).
    """

    # on_delete=CASCADE -> kalau user dihapus, keanggotaan kampusnya ikut terhapus.
    # related_name='campus' -> dari objek user bisa akses: user.campus.university
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='campus')
    # ForeignKey = banyak user boleh menunjuk ke 1 kampus yang sama (relasi many-to-one).
    # related_name='members' -> dari kampus bisa akses: university.members.all()
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='members')
    # auto_now_add=True -> diisi otomatis dengan waktu sekarang saat baris pertama kali dibuat.
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} @ {self.university.short_name}"


class Canteen(models.Model):
    """Satu kantin yang muncul sebagai pin di peta Community."""

    name = models.CharField(max_length=100)       # contoh: "Kantin Kancil"
    faculty = models.CharField(max_length=50)     # contoh: "Fasilkom" (dipakai filter fakultas di peta)
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='canteens')
    # DecimalField(max_digits=9, decimal_places=6) -> angka seperti -6.364520 (presisi ~10 cm).
    # Pakai Decimal (bukan Float) supaya koordinat tersimpan persis tanpa error pembulatan.
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    # Jangkauan kantin dalam meter. Kalau user berdiri lebih jauh dari ini, kantin tidak
    # direkomendasikan otomatis (lihat community.nearest_canteens, alasan 'far').
    radius_m = models.PositiveIntegerField(default=150)
    # Kantin yang dinonaktifkan tidak tampil di peta dan tidak bisa dipilih.
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.faculty})"

    class Meta:
        # Urut per fakultas dulu, lalu nama kantin.
        ordering = ['faculty', 'name']


class CommunityPost(models.Model):
    """Satu foto makanan yang dibagikan user ke peta Community (dibuat dari hasil scan)."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_posts')
    # ImageField -> file foto disimpan di folder media/community/<tahun>/<bulan>/
    photo = models.ImageField(upload_to='community/%Y/%m/', blank=True)
    # Foto data awal (showcase) disimpan sebagai file static di repo, bukan di media/,
    # supaya selalu ikut ter-deploy. Isinya path relatif static, contoh 'social/seed/kancil_1.jpg'.
    seed_image = models.CharField(max_length=200, blank=True)
    # ManyToMany -> 1 post bisa berisi banyak FoodLog (1 foto = beberapa makanan),
    # dan ditulis sebagai string 'scanner.FoodLog' karena model itu milik app scanner.
    food_logs = models.ManyToManyField('scanner.FoodLog', blank=True, related_name='community_posts')
    # Total emisi semua makanan di foto ini (gram CO2). Dipakai untuk warna pin & rata-rata kantin.
    total_co2_grams = models.FloatField(default=0)
    # on_delete=SET_NULL -> kalau kantin dihapus, post TIDAK ikut terhapus; kolom ini jadi kosong (NULL).
    # null=True wajib ada supaya database boleh menyimpan NULL.
    canteen = models.ForeignKey(Canteen, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    # Diisi kalau user memilih "Lainnya" (makan di luar daftar kantin).
    custom_location = models.CharField(max_length=100, blank=True)
    food_name = models.CharField(max_length=100, blank=True)
    # PositiveIntegerField -> harga tidak boleh negatif. null=True -> harga boleh tidak diisi.
    price = models.PositiveIntegerField(null=True, blank=True)
    # is_shared  : True kalau user mencentang "Bagikan ke Community".
    # is_hidden  : True kalau admin menyembunyikan post (lihat action di admin.py).
    # Post hanya tampil di peta kalau is_shared=True DAN is_hidden=False.
    is_shared = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # `or 'Tanpa nama'` -> kalau food_name kosong, tampilkan teks pengganti.
        return f"{self.user.username} - {self.food_name or 'Tanpa nama'}"

    class Meta:
        # Tanda minus = urut menurun -> post terbaru di atas.
        ordering = ['-created_at']


class PostReport(models.Model):
    """Laporan dari user bahwa sebuah post tidak pantas."""

    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='reports')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_reports')
    reason = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # post_id = id post langsung dari kolom FK (tanpa query tambahan ke tabel post).
        return f"Laporan {self.user.username} untuk post #{self.post_id}"

    class Meta:
        # Kombinasi (post, user) harus unik -> 1 user hanya bisa melapor 1 post sekali.
        unique_together = ['post', 'user']


class Friendship(models.Model):
    """Satu baris = satu hubungan antara dua user (arah: pengirim -> penerima).

    Siklus hidup:
        kirim permintaan  -> status PENDING
        penerima Terima   -> status ACCEPTED (berteman)
        penerima Tolak    -> status REJECTED (boleh dikirim ulang nanti)
        unfriend / batal  -> baris dihapus
    Semua aturan ini ada di social/friends.py, bukan di sini.
    """

    # Konstanta supaya di kode lain cukup menulis Friendship.PENDING (bukan string 'pending'
    # yang rawan typo).
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    # choices -> pasangan (nilai di database, label yang ditampilkan ke manusia).
    STATUS_CHOICES = [
        (PENDING, 'Menunggu'),
        (ACCEPTED, 'Berteman'),
        (REJECTED, 'Ditolak'),
    ]

    # Ada 2 FK ke tabel User yang sama, jadi related_name WAJIB beda supaya tidak bentrok:
    #   user.friend_requests_sent.all()      -> permintaan yang user kirim
    #   user.friend_requests_received.all()  -> permintaan yang user terima
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_requests_sent')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_requests_received')
    # default=PENDING -> setiap baris baru otomatis berstatus "menunggu".
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    # Waktu penerima menjawab (terima/tolak). Kosong selama masih PENDING.
    responded_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({self.status})"

    def other(self, user):
        """Kembalikan "orang satunya" dari hubungan ini, dilihat dari sisi `user`.

        Contoh: baris iqbal -> budi.
            other(iqbal) = budi
            other(budi)  = iqbal
        Membandingkan from_user_id (angka) lebih hemat daripada from_user (perlu query).
        """
        return self.to_user if self.from_user_id == user.id else self.from_user

    class Meta:
        ordering = ['-created_at']
        constraints = [
            # Database menolak 2 baris dengan pasangan (from_user, to_user) yang sama.
            # Karena aturan ini, kirim ulang setelah ditolak MEMAKAI ULANG baris lama
            # (lihat bagian akhir friends.send_request), bukan membuat baris baru.
            models.UniqueConstraint(fields=['from_user', 'to_user'], name='unique_friend_request'),
        ]
