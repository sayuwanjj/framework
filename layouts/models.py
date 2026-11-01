"""Модель макета, отправленного клиенту на согласование."""

from datetime import date, timedelta

from django.db import models

from participants.models import Client, Designer


class Layout(models.Model):
    """Макет: связан с одним дизайнером и одним клиентом."""

    STATUS_REVIEW = "На согласовании"
    STATUS_REVISION = "На доработке"
    STATUS_APPROVED = "Утверждён"
    STATUSES = [STATUS_REVIEW, STATUS_REVISION, STATUS_APPROVED]
    STATUS_CHOICES = [
        (STATUS_REVIEW, STATUS_REVIEW),
        (STATUS_REVISION, STATUS_REVISION),
        (STATUS_APPROVED, STATUS_APPROVED),
    ]

    title = models.CharField(
        max_length=200,
        verbose_name="Название макета",
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
        self.deadline = self.sent_date + timedelta(days=self.approval_days)
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

    def __str__(self) -> str:
        return f"{self.title} (версия {self.version})"
