from django import forms
from django.contrib.auth.models import User

from .models import Badge

class BadgeForm(forms.ModelForm):
    class Meta:
        model = Badge
        fields = [
            'name',
            'description',
            'icon',
            'criteria_type',
            'threshold'
        ]
        labels = {
            'name': 'Nama Lencana',
            'description': 'Deskripsi Lencana...',
            'icon': 'Ikon Lencana...',
            'criteria_type': 'Kriteria Lencana...',
            'threshold': 'Nilai Untuk Memperoleh Lencana...'
        }