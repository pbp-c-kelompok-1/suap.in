from django import forms
from .models import CampusMembership


class CampusForm(forms.ModelForm):
    class Meta:
        model = CampusMembership
        fields = ['university']
        labels = {'university': 'Kampus kamu'}
        widgets = {'university': forms.Select(attrs={'class': 'input-neu'})}
