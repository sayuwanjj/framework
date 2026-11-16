"""Фильтрация, создание и редактирование макетов средствами Django Forms."""
from django import forms
from django.utils import timezone

from layouts.models import Layout
from participants.models import Client, Designer

SORT_CHOICES = (
    ("deadline", "сроку согласования"),
    ("sent", "дате отправки (сначала новые)"),
    ("title", "названию"),
    ("client", "клиенту"),
    ("designer", "дизайнеру"),
)


class BootstrapFormMixin:
    """Единое оформление обычной формы и ModelForm."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                css_class = "form-check-input"
            elif isinstance(field.widget, forms.Select):
                css_class = "form-select"
            else:
                css_class = "form-control"
            field.widget.attrs.setdefault("class", css_class)


class LayoutFilterForm(BootstrapFormMixin, forms.Form):
    """GET-форма не изменяет записи, а проверяет условия выборки."""

    status = forms.ChoiceField(
        label="Статус", required=False,
        choices=[("", "Все статусы"), *Layout.Status.choices],
    )
    designer = forms.ModelChoiceField(
        label="Дизайнер", required=False,
        queryset=Designer.objects.order_by("name"),
        empty_label="Все дизайнеры",
    )
    client = forms.ModelChoiceField(
        label="Клиент", required=False,
        queryset=Client.objects.order_by("name"), empty_label="Все клиенты",
    )
    date = forms.DateField(
        label="Дата отправки", required=False,
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        input_formats=["%Y-%m-%d"],
    )
    sort = forms.ChoiceField(
        label="Сортировать по", choices=SORT_CHOICES, required=False,
        initial="deadline",
    )
    active_only = forms.BooleanField(
        label="Только активные согласования", required=False,
    )


class LayoutForm(BootstrapFormMixin, forms.ModelForm):
    """Внешние поля перечислены явно; статус и версия задаются моделью."""

    class Meta:
        model = Layout
        fields = (
            "title", "designer", "client", "sent_date",
            "approval_days", "image",
        )
        labels = {"title": "Название макета", "image": "Изображение макета"}
        help_texts = {
            "title": "Укажите понятное название, не менее трёх символов.",
            "sent_date": "Новая дата отправки не может быть в прошлом.",
            "approval_days": (
                "От 1 до 365 дней. Срок ответа вычисляется автоматически."
            ),
            "image": "Необязательно. PNG, JPEG или WebP, не более 5 МБ.",
        }
        widgets = {
            "title": forms.TextInput(
                attrs={"placeholder": "Например, Главная страница"}
            ),
            "sent_date": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d",
            ),
            "approval_days": forms.NumberInput(attrs={"min": 1, "max": 365}),
            "image": forms.ClearableFileInput(
                attrs={"accept": "image/png,image/jpeg,image/webp"},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_date = (
            self.instance.sent_date if self.instance.pk else None
        )
        self.fields["sent_date"].input_formats = ["%Y-%m-%d"]
        self.fields["approval_days"].min_value = 1
        self.fields["approval_days"].max_value = 365
        self.fields["designer"].queryset = Designer.objects.order_by("name")
        self.fields["client"].queryset = Client.objects.order_by("name")
        if not self.instance.pk:
            self.initial.setdefault("sent_date", timezone.localdate())
            self.initial.setdefault("approval_days", 7)

    def clean_title(self):
        title = " ".join(self.cleaned_data["title"].split())
        if len(title) < 3:
            raise forms.ValidationError(
                "Название должно содержать не менее 3 символов.")
        return title

    def clean_sent_date(self):
        sent_date = self.cleaned_data["sent_date"]
        if (sent_date < timezone.localdate()
                and sent_date != self.original_date):
            raise forms.ValidationError(
                "Нельзя назначить новую дату отправки в прошлом.")
        return sent_date

    def clean_approval_days(self):
        days = self.cleaned_data["approval_days"]
        if not 1 <= days <= 365:
            raise forms.ValidationError(
                "Срок согласования должен быть от 1 до 365 дней.")
        return days

    def clean(self):
        cleaned = super().clean()
        names = ("title", "designer", "client", "sent_date")
        if all(name in cleaned for name in names):
            conflicts = Layout.objects.active().filter(
                **{name: cleaned[name] for name in names}
            )
            if self.instance.pk:
                conflicts = conflicts.exclude(pk=self.instance.pk)
            if conflicts.exists():
                raise forms.ValidationError(
                    "Активная заявка на этот макет для выбранных участников "
                    "и даты уже существует. Измените условия "
                    "или отмените прежнюю заявку."
                )
        return cleaned
