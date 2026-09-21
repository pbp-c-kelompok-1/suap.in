from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        specs = {
            'username': ('Username', 'username'),
            'email': ('Email', 'email'),
            'password1': ('Password', 'new-password'),
            'password2': ('Confirm password', 'new-password'),
        }
        for name, (placeholder, autocomplete) in specs.items():
            self.fields[name].widget.attrs.update({
                'class': 'input-neu',
                'placeholder': placeholder,
                'autocomplete': autocomplete,
            })
            self.fields[name].help_text = ''

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Email ini sudah terdaftar.')
        return email


class LoginForm(forms.Form):
    identifier = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'input-neu',
            'placeholder': 'Enter your email or username',
            'autocomplete': 'username',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input-neu',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
        })
    )
    remember = forms.BooleanField(required=False)


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'input-neu',
            'placeholder': 'Enter your email',
            'autocomplete': 'email',
        })
    )


class OtpForm(forms.Form):
    code = forms.CharField(
        min_length=6,
        max_length=6,
        widget=forms.TextInput(attrs={
            'class': 'input-neu',
            'placeholder': '000000',
            'inputmode': 'numeric',
            'autocomplete': 'one-time-code',
            'maxlength': '6',
            'style': 'text-align:center;letter-spacing:0.6em;font-weight:800;font-size:1.5rem;',
        })
    )

    def clean_code(self):
        code = self.cleaned_data['code'].strip()
        if not code.isdigit():
            raise forms.ValidationError('Kode harus berupa 6 digit angka.')
        return code


class NewPasswordForm(forms.Form):
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input-neu',
            'placeholder': 'New password',
            'autocomplete': 'new-password',
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input-neu',
            'placeholder': 'Confirm new password',
            'autocomplete': 'new-password',
        })
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get('password1')
        password2 = cleaned.get('password2')
        if password1 and password2:
            if password1 != password2:
                self.add_error('password2', 'Konfirmasi password tidak sama.')
            else:
                try:
                    validate_password(password1, self.user)
                except forms.ValidationError as error:
                    self.add_error('password1', error)
        return cleaned
