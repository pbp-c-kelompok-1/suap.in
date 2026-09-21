from django import forms


class FoodScanForm(forms.Form):
    photo = forms.ImageField(
        label='Foto Makanan',
        widget=forms.FileInput(attrs={
            'accept': 'image/*',
            'class': 'hidden',
            'id': 'photo-input'
        })
    )


class ManualCorrectionForm(forms.Form):
    item_name = forms.CharField(max_length=200, label='Nama Makanan')
    co2_grams = forms.FloatField(min_value=0, label='Estimasi CO2 (gram)')
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
        label='Catatan'
    )
