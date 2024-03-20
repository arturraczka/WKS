from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(max_length=254, label="Nazwa użytkownika", widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control', 'placeholder': 'Username or Email'}))

    # username = forms.CharField(max_length=254, label="Nazwa użytkownika", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'login'}))
    password = forms.CharField(label="Hasło", widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'hasło'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.include_media = True
        self.helper.form_class = ''
        self.helper.tag = None
        self.helper.wrapper_class = None
        self.helper.add_input(Submit('submit', 'Zaloguj'))


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="E-mail",
        max_length=254,
        widget=forms.EmailInput(attrs={'autofocus': True, 'autocomplete': 'email', 'class': 'form-control', 'placeholder': 'Wpisz swój email'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.include_media = True
        self.helper.form_class = ''
        self.helper.tag = None
        self.helper.wrapper_class = None
        self.helper.add_input(Submit('submit', 'Zmień hasło'))


class CustomSetPasswordForm(SetPasswordForm):
    error_messages = {
        "password_mismatch": "Dwa hasła nie są takie same.",
    }
    new_password1 = forms.CharField(
        label="Nowe hasło",
        widget=forms.PasswordInput(attrs={'autofocus': True, "autocomplete": "new-password"}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label="Potwierdź nowe hasło",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.include_media = True
        self.helper.form_class = ''
        self.helper.tag = None
        self.helper.wrapper_class = None
        self.helper.add_input(Submit('submit', 'Ustaw hasło'))
