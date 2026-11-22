"""Проверка фильтров и пользовательских данных макета."""
from django import forms
from django.utils import timezone

from layouts.models import Layout
from participants.models import Client, Designer

SORT_CHOICES = [('deadline', 'Сроку'), ('sent', 'Дате отправки'),
                ('title', 'Названию'), ('client', 'Клиенту'),
                ('designer', 'Дизайнеру')]


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = (
                'form-check-input' if isinstance(
                    field.widget, forms.CheckboxInput)
                else 'form-select' if isinstance(field.widget, forms.Select)
                else 'form-control')


class LayoutFilterForm(BootstrapFormMixin, forms.Form):
    status = forms.ChoiceField(required=False, label='Статус', choices=[
        ('', 'Все статусы'), *Layout.Status.choices])
    designer = forms.ModelChoiceField(
        queryset=Designer.objects.order_by('name'), required=False,
        label='Дизайнер', empty_label='Все дизайнеры')
    client = forms.ModelChoiceField(
        queryset=Client.objects.order_by('name'), required=False,
        label='Клиент', empty_label='Все клиенты')
    date = forms.DateField(required=False, label='Дата отправки',
                           input_formats=['%Y-%m-%d'], widget=forms.DateInput(
                               attrs={'type': 'date'}, format='%Y-%m-%d'))
    sort = forms.ChoiceField(required=False, choices=SORT_CHOICES,
                             initial='deadline', label='Сортировать по')
    active_only = forms.BooleanField(required=False,
                                     label='Только активные согласования')


class LayoutForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Layout
        fields = ('title', 'designer', 'client', 'sent_date',
                  'approval_days', 'image')
        help_texts = {
            'title': 'Не менее трёх символов.',
            'sent_date': 'Новая дата отправки не может быть в прошлом.',
            'approval_days': 'От 1 до 365 дней.',
            'image': 'PNG, JPEG или WebP до 5 МБ. Необязательно.',
        }
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Название макета'}),
            'sent_date': forms.DateInput(attrs={'type': 'date'},
                                         format='%Y-%m-%d'),
            'approval_days': forms.NumberInput(attrs={'min': 1, 'max': 365}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_date = (
            self.instance.sent_date if self.instance.pk else None)
        if not self.instance.pk:
            self.initial.setdefault('sent_date', timezone.localdate())
            self.initial.setdefault('approval_days', 7)

    def clean_title(self):
        title = ' '.join(self.cleaned_data['title'].split())
        if len(title) < 3:
            raise forms.ValidationError('Название короче трёх символов.')
        return title

    def clean_sent_date(self):
        value = self.cleaned_data['sent_date']
        if value < timezone.localdate() and value != self.original_date:
            raise forms.ValidationError('Новая дата не может быть в прошлом.')
        return value

    def clean_approval_days(self):
        value = self.cleaned_data['approval_days']
        if not 1 <= value <= 365:
            raise forms.ValidationError('Укажите срок от 1 до 365 дней.')
        return value

    def clean(self):
        cleaned = super().clean()
        names = ('title', 'designer', 'client', 'sent_date')
        if all(name in cleaned for name in names):
            conflicts = Layout.objects.active().filter(
                **{name: cleaned[name] for name in names})
            if self.instance.pk:
                conflicts = conflicts.exclude(pk=self.instance.pk)
            if conflicts.exists():
                raise forms.ValidationError(
                    'Активная заявка с этими участниками, названием '
                    'и датой уже существует.')
        return cleaned
