from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, UsernameField


class RegisterUserForm(forms.ModelForm):
    password = forms.CharField(
        min_length=8, max_length=128, widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': '********',
                'id': 'user_password',
            }
        )
    )

    username = UsernameField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Введите логин', 'id': 'user_username'}))

    class Meta:
        model = User
        fields = ('username', 'password')
        labels = {'username': 'Login', 'password': 'Password'}
        help_texts = {'username': '123', 'password': ''}

    def save(self, commit=True):
        user = super(RegisterUserForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)

    username = UsernameField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Введите логин', 'id': 'user_username'}))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={
            'class': 'form-control',
            'placeholder': '********',
            'id': 'user_password',
        }
    ))


class NumberInputForm(forms.Form):
    number = forms.IntegerField(min_value=1, max_value=20, widget=forms.NumberInput(
        attrs={
            'class': 'answer',
        }
    ))