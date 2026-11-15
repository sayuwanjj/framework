"""Модель макета, отправленного клиенту на согласование."""

from datetime import date, timedelta
from uuid import uuid4

from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from participants.models import Client, Designer


class LayoutQuerySet(models.QuerySet):
    """Переиспользуемые условия предметной области."""

    def active(self):
        return self.exclude(status=Layout.Status.APPROVED)

    def overdue(self, on_date):
        return self.active().filter(deadline__lt=on_date)


class Layout(models.Model):
    """Макет: связан с одним дизайнером и одним клиентом."""

    class Status(models.TextChoices):
        REVIEW = "REVIEW", "На согласовании"
        REVISION = "REVISION", "На доработке"
        APPROVED = "APPROVED", "Утверждён"

    STATUS_REVIEW = Status.REVIEW
    STATUS_REVISION = Status.REVISION
    STATUS_APPROVED = Status.APPROVED
    STATUSES = Status.values
    STATUS_CHOICES = Status.choices
    objects = LayoutQuerySet.as_manager()

    title = models.CharField(
        max_length=200,
        verbose_name="Название макета",
    )
    slug = models.SlugField(max_length=250, unique=True, blank=True,
                            verbose_name="Адрес макета")
    is_revised = models.GeneratedField(
        expression=models.Case(
            models.When(version__gt=1, then=models.Value(True)),
            default=models.Value(False),
            output_field=models.BooleanField(),
        ),
        output_field=models.BooleanField(),
        db_persist=True,
        verbose_name="Повторная версия",
    )
    version = models.PositiveIntegerField(
        default=1,
        verbose_name="Версия",
    )
    # Связь «многие к одному»: у дизайнера много макетов.
    # PROTECT запрещает удалить дизайнера, пока у него есть макеты.
    designer = models.ForeignKey(
        Designer,
        on_delete=models.PROTECT,
        related_name="layouts",
        verbose_name="Дизайнер",
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name="layouts",
        verbose_name="Клиент",
    )
    sent_date = models.DateField(
        verbose_name="Дата отправки",
    )
    approval_days = models.PositiveIntegerField(
        verbose_name="Срок согласования, дней",
    )
    # Срок ответа клиента вычисляется в save() и хранится в базе,
    # чтобы по нему можно было фильтровать и сортировать через ORM.
    deadline = models.DateField(
        editable=False,
        verbose_name="Срок ответа клиента",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_REVIEW,
        verbose_name="Статус",
    )

    class Meta:
        ordering = ["deadline", "pk"]
        verbose_name = "Макет"
        verbose_name_plural = "Макеты"

    def save(self, *args, **kwargs):
        """Пересчитать срок согласования и сохранить макет."""
        if not self.slug:
            base = slugify(self.title)[:200] or "layout"
            self.slug = f"{base}-{uuid4().hex}"
            if kwargs.get("update_fields") is not None:
                kwargs["update_fields"] = set(
                    kwargs["update_fields"]) | {"slug"}
        self.deadline = self.sent_date + timedelta(days=self.approval_days)
        update_fields = kwargs.get("update_fields")
        if update_fields is not None and {
                "sent_date", "approval_days"}.intersection(update_fields):
            kwargs["update_fields"] = set(update_fields) | {"deadline"}
        super().save(*args, **kwargs)

    @property
    def is_approved(self) -> bool:
        """Признак того, что макет утверждён."""
        return self.status == Layout.STATUS_APPROVED

    def days_left(self, today: date) -> int:
        """Число дней, оставшихся до окончания срока согласования."""
        return (self.deadline - today).days

    def approve(self) -> None:
        """Утвердить макет и сохранить только поле status."""
        if self.is_approved:
            raise ValueError("Макет уже утверждён")
        self.status = Layout.STATUS_APPROVED
        self.save(update_fields=["status"])

    def send_to_revision(self) -> None:
        """Отправить макет на доработку: новая версия и новый статус."""
        if self.is_approved:
            raise ValueError("Утверждённый макет не дорабатывается")
        self.status = Layout.STATUS_REVISION
        self.version += 1
        self.save(update_fields=["status", "version"])

    def get_absolute_url(self):
        return reverse("layouts:detail_by_slug", kwargs={"slug": self.slug})

    def __str__(self) -> str:
        return f"{self.title} (версия {self.version})"
