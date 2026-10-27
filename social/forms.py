from django import forms
from .models import CampusMembership


class CampusForm(forms.ModelForm):
    class Meta:
        model = CampusMembership
        fields = ['university']
        labels = {'university': 'Kampus kamu'}
        widgets = {'university': forms.Select(attrs={
            'style': 'width:100%;border:0;border-radius:16px;background:var(--bg);color:var(--text);font:inherit;font-weight:700;padding:12px 16px;box-shadow:inset 4px 4px 9px var(--sh-d),inset -4px -4px 9px var(--sh-l)',
        })}
