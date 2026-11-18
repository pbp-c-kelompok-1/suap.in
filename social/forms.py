"""Django Forms modul Social = tempat VALIDASI input dari user.

Cara kerja Form Django:
    form = SomeForm(request.POST)   # isi form dengan data yang dikirim browser
    form.is_valid()                 # jalankan semua pengecekan; True kalau lolos semua
    form.cleaned_data['field']      # data yang sudah bersih & aman dipakai
    form.errors                     # pesan error per field kalau tidak valid

Urutan pengecekan saat is_valid():
    1. Cek bawaan tiap field (wajib diisi? panjang maksimal? pilihan valid?)
    2. Method clean_<nama_field>() kalau ada -> pengecekan buatan kita sendiri
"""
from django import forms
from django.contrib.auth.models import User

from .models import CampusMembership


class CampusForm(forms.ModelForm):
    """Form pilih kampus (Create/Update CampusMembership).

    ModelForm = form yang dibuat OTOMATIS dari model. Field 'university' otomatis
    menjadi dropdown berisi semua University, dan form.save() langsung menyimpan ke tabel.
    """

    class Meta:
        model = CampusMembership          # form ini untuk model CampusMembership
        fields = ['university']           # hanya field ini yang boleh diisi user (user diisi di view)
        labels = {'university': 'Kampus kamu'}
        # Ganti pesan error bawaan Django (bahasa Inggris) dengan bahasa Indonesia.
        error_messages = {'university': {
            'required': 'Pilih kampus dulu.',                 # dropdown tidak dipilih
            'invalid_choice': 'Kampus tidak ditemukan.',      # id kampus yang dikirim tidak ada
        }}
        # widgets = mengatur tampilan HTML field (di sini hanya styling dropdown).
        widgets = {'university': forms.Select(attrs={
            'style': 'width:100%;border:0;border-radius:16px;background:var(--bg);color:var(--text);font:inherit;font-weight:700;padding:12px 16px;box-shadow:inset 4px 4px 9px var(--sh-d),inset -4px -4px 9px var(--sh-l)',
        })}


class FriendRequestForm(forms.Form):
    """Create Friendship: validasi username tujuan sebelum permintaan dibuat.

    forms.Form biasa (bukan ModelForm) karena form ini tidak langsung menyimpan ke tabel;
    penyimpanannya dilakukan friends.send_request.
    """

    # CharField -> input teks. max_length=150 sama dengan batas username bawaan Django.
    username = forms.CharField(max_length=150, error_messages={'required': 'Username wajib diisi.'})

    def __init__(self, *args, sender=None, **kwargs):
        """Tambahan parameter `sender` (user yang sedang login).

        Dipanggil di view: FriendRequestForm(request.POST, sender=request.user)
        *args / **kwargs diteruskan ke __init__ bawaan Form lewat super().
        """
        super().__init__(*args, **kwargs)
        self.sender = sender      # disimpan supaya bisa dipakai di clean_username
        self.receiver = None      # nanti diisi objek User tujuan kalau username valid

    def clean_username(self):
        """Dipanggil otomatis oleh is_valid() (aturan Django: clean_<nama_field>).
#username__iexact=username
        Mengecek:
            1. username ada di database
            2. bukan diri sendiri
        Kalau gagal -> raise ValidationError -> pesan masuk ke form.errors.
        Kalau lolos -> simpan User tujuan ke self.receiver dan kembalikan nilai bersihnya.
        """
        # .strip() -> buang spasi di depan/belakang ("  budi " -> "budi").
        username = self.cleaned_data['username'].strip()
        # .first() -> objek User atau None (tidak melempar error seperti .get()).
        receiver = User.objects.filter(username=username).first()
        if receiver is None:
            raise forms.ValidationError(f'User "{username}" tidak ditemukan.')
        if receiver == self.sender:
            raise forms.ValidationError('Kamu tidak bisa menambahkan dirimu sendiri.')
        self.receiver = receiver
        return username  # nilai return = nilai yang masuk ke cleaned_data['username']


class FriendResponseForm(forms.Form):
    """Update Friendship: hanya boleh 'accept' (terima) atau 'reject' (tolak)."""

    # ChoiceField -> nilai yang dikirim HARUS salah satu dari choices.
    # Kalau browser (atau orang iseng) mengirim action=hapus, otomatis invalid_choice.
    action = forms.ChoiceField(
        choices=[('accept', 'Terima'), ('reject', 'Tolak')],
        error_messages={'required': 'Pilih terima atau tolak.',
                        'invalid_choice': 'Pilihan harus terima atau tolak.'},
    )

    @property
    def accept(self):
        """True kalau user memilih Terima. @property -> dipanggil tanpa kurung: form.accept"""
        return self.cleaned_data['action'] == 'accept'


def first_error(form):
    """Pesan error pertama dari form, untuk ditampilkan sebagai satu kalimat.

    form.errors bentuknya seperti {'username': ['User "x" tidak ditemukan.']}.
    Loop ini mengambil pesan pertama dari field pertama lalu langsung return.
    Kalau entah kenapa tidak ada error, pakai pesan umum.
    """
    for errors in form.errors.values():
        return errors[0]
    return 'Data tidak valid.'
