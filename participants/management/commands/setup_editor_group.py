"""Создать воспроизводимую группу редакторов предметных данных сервиса."""
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q


class Command(BaseCommand):
    help = "Создать группу редакторов макетов, комментариев и участников."

    @transaction.atomic
    def handle(self, *args, **options):
        group, _ = Group.objects.get_or_create(name="Редакторы сервиса")
        permissions = Permission.objects.filter(
            Q(content_type__app_label="layouts", content_type__model="layout")
            | Q(content_type__app_label="comments",
                content_type__model="comment")
            | Q(content_type__app_label="participants",
                content_type__model__in=["designer", "client"])
        ).filter(codename__regex=r"^(add|change|delete|view)_")
        group.permissions.set(permissions)
        self.stdout.write(self.style.SUCCESS(
            f"Группа «{group.name}» настроена: {permissions.count()} прав."
        ))
