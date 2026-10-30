from django import forms
from django.contrib.auth.models import User

from .models import CampusMembership


class CampusForm(forms.ModelForm):
    class Meta:
        model = CampusMembership
        fields = ['university']
        labels = {'university': 'Kampus kamu'}
        error_messages = {'university': {
            'required': 'Pilih kampus dulu.',
            'invalid_choice': 'Kampus tidak ditemukan.',
        }}
        widgets = {'university': forms.Select(attrs={
            'style': 'width:100%;border:0;border-radius:16px;background:var(--bg);color:var(--text);font:inherit;font-weight:700;padding:12px 16px;box-shadow:inset 4px 4px 9px var(--sh-d),inset -4px -4px 9px var(--sh-l)',
        })}


class FriendRequestForm(forms.Form):
    """Create Friendship: validasi username tujuan sebelum permintaan dibuat."""

    username = forms.CharField(max_length=150, error_messages={'required': 'Username wajib diisi.'})

    def __init__(self, *args, sender=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.sender = sender
        self.receiver = None

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        receiver = User.objects.filter(username=username).first()
        if receiver is None:
            raise forms.ValidationError(f'User "{username}" tidak ditemukan.')
        if receiver == self.sender:
            raise forms.ValidationError('Kamu tidak bisa menambahkan dirimu sendiri.')
        self.receiver = receiver
        return username


class FriendResponseForm(forms.Form):
    """Update Friendship: hanya boleh 'accept' (terima) atau 'reject' (tolak)."""

    action = forms.ChoiceField(
        choices=[('accept', 'Terima'), ('reject', 'Tolak')],
        error_messages={'required': 'Pilih terima atau tolak.',
                        'invalid_choice': 'Pilihan harus terima atau tolak.'},
    )

    @property
    def accept(self):
        return self.cleaned_data['action'] == 'accept'


def first_error(form):
    """Pesan error pertama dari form, untuk ditampilkan sebagai satu kalimat."""
    for errors in form.errors.values():
        return errors[0]
    return 'Data tidak valid.'
