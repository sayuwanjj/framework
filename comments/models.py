"""Модель комментария клиента к макету."""

from django.db import models

from layouts.models import Layout
from participants.models import Client


class Comment(models.Model):
    """Замечание клиента к конкретной версии макета."""

    # CASCADE: комментарии не имеют смысла без макета,
    # поэтому удаляются вместе с ним.
    layout = models.ForeignKey(
        Layout,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Макет",
    )
    # PROTECT: клиента нельзя удалить, пока есть его комментарии.
    author = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name="comments",
        verbose_name="Автор",
    )
    text = models.TextField(
        verbose_name="Текст комментария",
    )
    comment_date = models.DateField(
        verbose_name="Дата комментария",
    )
    layout_version = models.PositiveIntegerField(
        verbose_name="Версия макета",
    )

    class Meta:
        ordering = ["comment_date", "pk"]
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"

    def __str__(self) -> str:
        return f"{self.author} — {self.layout}: {self.text[:30]}"
