from django import forms
from django.contrib.auth.models import User

from .models import FriendChallenge, StoryComic, StoryPage


class FriendChallengeForm(forms.ModelForm):
    class Meta:
        model = FriendChallenge
        fields = ['opponent', 'metric', 'duration_days']
        labels = {
            'opponent': 'Tantang siapa?',
            'metric': 'Adu apa?',
            'duration_days': 'Durasi',
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # lawan harus aktif dan gk boleh diri sendiri
        self.fields['opponent'].queryset = (
            User.objects.filter(is_active=True)
            .exclude(pk=user.pk)
            .order_by('username')
            if user is not None
            else User.objects.none()
        )


class StoryComicForm(forms.ModelForm):
    class Meta:
        model = StoryComic
        fields = ['bab', 'title', 'description', 'unlock_level', 'is_published']
        labels = {
            'bab': 'Nomor bab', 'title': 'Judul bab', 'description': 'Ringkasan cerita',
            'unlock_level': 'Terbuka mulai level', 'is_published': 'Terbitkan bab',
        }
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # chapter baru mulai dari draft, isinya dilengkapi dulu sebelum diterbitkan
        if self.instance._state.adding:
            self.fields['is_published'].initial = False
        self.fields['is_published'].help_text = 'Tambahkan setidaknya satu halaman sebelum menerbitkan bab.'

    def clean(self):
        data = super().clean()
        # jangan sampe ada chapter terbit yang blm punya halaman
        if data.get('is_published') and (self.instance._state.adding or not self.instance.pages.exists()):
            self.add_error('is_published', 'Simpan sebagai draft dan tambahkan halaman terlebih dahulu.')
        return data


class StoryPageForm(forms.ModelForm):
    class Meta:
        model = StoryPage
        fields = ['position', 'title', 'scene', 'narration', 'speaker_one', 'dialogue_one',
                  'speaker_two', 'dialogue_two', 'takeaway', 'action', 'source_label', 'source_url']
        labels = {
            'position': 'Urutan halaman', 'title': 'Judul halaman', 'scene': 'Latar ilustrasi',
            'narration': 'Narasi pembuka', 'speaker_one': 'Tokoh pertama', 'dialogue_one': 'Dialog tokoh pertama',
            'speaker_two': 'Tokoh kedua', 'dialogue_two': 'Dialog tokoh kedua',
            'takeaway': 'Pelajaran halaman ini', 'action': 'Langkah kecil untuk pembaca',
            'source_label': 'Nama referensi', 'source_url': 'Tautan referensi',
        }
        widgets = {name: forms.Textarea(attrs={'rows': 3}) for name in
                   ['narration', 'dialogue_one', 'dialogue_two', 'takeaway']}

    def __init__(self, *args, comic, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.comic = comic
        self.comic = comic

    def clean_position(self):
        position = self.cleaned_data['position']
        # Urutan yang sama gk boleh dipakai 2 halaman di bab yg sama
        if self.comic.pages.filter(position=position).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Urutan ini sudah dipakai halaman lain di bab yang sama.')
        return position

    def clean(self):
        data = super().clean()
        url, label = data.get('source_url'), data.get('source_label')
        if url and not url.startswith(('https://', 'http://')):
            self.add_error('source_url', 'Gunakan tautan HTTP atau HTTPS.')
        if bool(url) != bool(label):
            self.add_error('source_url', 'Isi nama dan tautan referensi secara berpasangan, atau kosongkan keduanya.')
        return data
