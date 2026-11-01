"""Инспекция исходной базы ПР7 перед переносом данных в Django ORM.

Запуск из корня проекта:

    python db/inspect_source_db.py

Скрипт только читает базу data/layout_service.sqlite: выводит таблицы,
столбцы, количество записей и проверяет ссылки внешних ключей.
"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_DB = BASE_DIR / "data" / "layout_service.sqlite"

# Запросы проверки ссылок: строки, которые ссылаются на
# несуществующие записи. Для корректной базы результат — 0.
BROKEN_LINKS = {
    "layouts.designer_id": """
        SELECT COUNT(*) FROM layouts
        WHERE designer_id NOT IN (SELECT id FROM designers)
    """,
    "layouts.client_id": """
        SELECT COUNT(*) FROM layouts
        WHERE client_id NOT IN (SELECT id FROM clients)
    """,
    "comments.layout_id": """
        SELECT COUNT(*) FROM comments
        WHERE layout_id NOT IN (SELECT id FROM layouts)
    """,
    "comments.author_id": """
        SELECT COUNT(*) FROM comments
        WHERE author_id NOT IN (SELECT id FROM clients)
    """,
}


def main() -> None:
    """Вывести структуру исходной базы и результаты проверок."""
    if not SOURCE_DB.exists():
        raise FileNotFoundError(f"Исходная база не найдена: {SOURCE_DB}")

    with sqlite3.connect(SOURCE_DB) as connection:
        connection.row_factory = sqlite3.Row
        tables = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

        for table in tables:
            # Имя таблицы берётся из sqlite_master, а не от пользователя.
            table_name = table["name"]
            print(f"\nТаблица: {table_name}")
            columns = connection.execute(
                f'PRAGMA table_info("{table_name}")'
            ).fetchall()
            for column in columns:
                print(
                    f"  {column['name']}: {column['type']}, "
                    f"NOT NULL={column['notnull']}, PK={column['pk']}"
                )
            count = connection.execute(
                f'SELECT COUNT(*) FROM "{table_name}"'
            ).fetchone()[0]
            print(f"  Количество записей: {count}")

        print("\nПроверка ссылок внешних ключей:")
        for link, query in BROKEN_LINKS.items():
            broken = connection.execute(query).fetchone()[0]
            print(f"  {link}: битых ссылок — {broken}")


if __name__ == "__main__":
    main()
