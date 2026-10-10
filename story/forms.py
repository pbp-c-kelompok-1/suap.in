from django import forms
from django.contrib.auth.models import User

from .models import FriendChallenge


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
        # Sementara semua user bisa ditantang; nanti diganti daftar teman dari modul social
        self.fields['opponent'].queryset = User.objects.exclude(pk=user.pk).order_by('username')
