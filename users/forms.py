from django import forms
from django.contrib.auth.forms import UserCreationForm
from users.models import User, Profile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    username = forms.CharField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.is_active = False
        if commit:
            user.save()
        return user


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('avatar', 'bio', 'birth_date', 'steam_id')
        labels = {
            'avatar': 'Аватар',
            'bio': 'О себе',
            'birth_date': 'Дата рождения',
            'steam_id': 'Steam ID',
        }
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Расскажите о себе...',
            }),
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'steam_id': forms.TextInput(attrs={
                'placeholder': 'Ваш Steam ID или ссылка на профиль',
            }),
        }