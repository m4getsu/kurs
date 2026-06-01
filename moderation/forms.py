from django import forms
from moderation.models import Report


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ('reason',)
        labels = {'reason': 'Причина жалобы'}
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Опишите нарушение...'}),
        }


class BanForm(forms.Form):
    banned_until = forms.DateTimeField(
        required=False,
        label='Заблокирован до',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        help_text='Оставьте пустым для бессрочной блокировки',
    )
    reason = forms.CharField(
        label='Причина',
        widget=forms.Textarea(attrs={'rows': 3}),
    )
