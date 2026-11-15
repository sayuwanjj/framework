"""Перенос данных из базы ПР7 в таблицы Django ORM (db.sqlite3).

Запуск из корня проекта после применения миграций:

    python db/import_sqlite_to_orm.py

Исходная база data/layout_service.sqlite только читается.
Идентификаторы записей сохраняются, поэтому связи не теряются.
Повторный запуск обновляет записи, а не создаёт дубликаты.
"""

import os
import sqlite3
import sys
from datetime import date
from pathlib import Path

import django
from django.db import transaction

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_DB = BASE_DIR / "data" / "layout_service.sqlite"

# Корень проекта нужен в путях поиска модулей, чтобы Django
# нашёл пакет настроек layout_service и приложения проекта.
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "layout_service.settings")
django.setup()


def read_rows(connection: sqlite3.Connection, query: str) -> list:
    """Выполнить запрос к исходной базе и вернуть все строки."""
    return connection.execute(query).fetchall()


def main() -> None:
    """Перенести дизайнеров, клиентов, макеты и комментарии."""
    # Модели импортируются только после django.setup().
    from comments.models import Comment
    from layouts.models import Layout
    from participants.models import Client, Designer

    if not SOURCE_DB.exists():
        raise FileNotFoundError(f"Исходная база не найдена: {SOURCE_DB}")

    with sqlite3.connect(SOURCE_DB) as connection:
        connection.row_factory = sqlite3.Row
        designers = read_rows(
            connection, "SELECT id, name, email FROM designers ORDER BY id"
        )
        clients = read_rows(
            connection,
            "SELECT id, name, email, company FROM clients ORDER BY id",
        )
        layouts = read_rows(
            connection,
            """
            SELECT id, title, version, designer_id, client_id,
                   sent_date, approval_days, status
            FROM layouts ORDER BY id
            """,
        )
        comments = read_rows(
            connection,
            """
            SELECT id, layout_id, author_id, text,
                   comment_date, layout_version
            FROM comments ORDER BY id
            """,
        )

    # Все записи сохраняются одной транзакцией: при ошибке
    # изменения откатываются и база не заполняется наполовину.
    with transaction.atomic():
        # Сначала независимые таблицы, на них ссылаются макеты.
        for row in designers:
            Designer.objects.update_or_create(
                pk=row["id"],
                defaults={"name": row["name"], "email": row["email"]},
            )
        for row in clients:
            Client.objects.update_or_create(
                pk=row["id"],
                defaults={
                    "name": row["name"],
                    "email": row["email"],
                    "company": row["company"] or "",
                },
            )
        # Затем макеты: строка ГГГГ-ММ-ДД превращается в объект date.
        for row in layouts:
            Layout.objects.update_or_create(
                pk=row["id"],
                defaults={
                    "title": row["title"],
                    "version": row["version"],
                    "designer_id": row["designer_id"],
                    "client_id": row["client_id"],
                    "sent_date": date.fromisoformat(row["sent_date"]),
                    "approval_days": row["approval_days"],
                    "status": {
                        "На согласовании": Layout.Status.REVIEW,
                        "На доработке": Layout.Status.REVISION,
                        "Утверждён": Layout.Status.APPROVED,
                    }.get(row["status"], row["status"]),
                },
            )
        # В конце комментарии: они ссылаются на макеты и клиентов.
        for row in comments:
            Comment.objects.update_or_create(
                pk=row["id"],
                defaults={
                    "layout_id": row["layout_id"],
                    "author_id": row["author_id"],
                    "text": row["text"],
                    "comment_date": date.fromisoformat(row["comment_date"]),
                    "layout_version": row["layout_version"],
                },
            )

    print("Перенос данных завершён.")
    print(f"Дизайнеров: {Designer.objects.count()}")
    print(f"Клиентов: {Client.objects.count()}")
    print(f"Макетов: {Layout.objects.count()}")
    print(f"Комментариев: {Comment.objects.count()}")


if __name__ == "__main__":
    main()
