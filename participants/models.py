"""Модели участников согласования: дизайнер и клиент."""

from django.db import models


class Designer(models.Model):
    """Дизайнер, который отправляет макеты на согласование."""

    # Имя дизайнера: строка ограниченной длины.
    name = models.CharField(
        max_length=300,
        verbose_name="Имя дизайнера",
    )
    # Почта: EmailField проверяет формат, unique запрещает повторы.
    email = models.EmailField(
        unique=True,
        verbose_name="Электронная почта",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Дизайнер"
        verbose_name_plural = "Дизайнеры"

    def __str__(self) -> str:
        return self.name


class Client(models.Model):
    """Клиент, который согласует макеты и оставляет комментарии."""

    name = models.CharField(
        max_length=200,
        verbose_name="Имя клиента",
    )
    email = models.EmailField(
        unique=True,
        verbose_name="Электронная почта",
    )
    # Компания необязательна: blank=True разрешает пустое значение
    # в формах, default="" хранит пустую строку вместо NULL.
    company = models.CharField(
        max_length=200,
        blank=True,
        default="",
        verbose_name="Компания",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"

    def __str__(self) -> str:
        return self.name
