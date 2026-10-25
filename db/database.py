"""Подключение к базе данных SQLite проекта."""

import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "layout_service.sqlite"
SCHEMA_PATH = BASE_DIR / "sql" / "schema.sql"


def get_connection(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    """Открыть соединение с базой данных и настроить его.

    row_factory = sqlite3.Row позволяет обращаться к полям результата
    по именам: row["title"] в Python и {{ row.title }} в шаблоне.
    PRAGMA foreign_keys = ON включает проверку внешних ключей,
    которая в SQLite по умолчанию выключена.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_tables(conn: sqlite3.Connection) -> None:
    """Создать таблицы, выполнив SQL-скрипт sql/schema.sql."""
    with open(SCHEMA_PATH, encoding="utf-8") as file:
        conn.executescript(file.read())


def main() -> None:
    """Создать файл базы и таблицы, затем вывести список таблиц.

    Запуск: python -m db.database [путь к файлу базы].
    Без аргумента используется рабочая база DB_PATH.
    """
    db_path = sys.argv[1] if len(sys.argv) > 1 else DB_PATH
    conn = get_connection(db_path)
    try:
        create_tables(conn)
        tables = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """
        ).fetchall()
    finally:
        conn.close()
    print(f"База данных: {db_path}")
    print("Таблицы:", ", ".join(row["name"] for row in tables))


if __name__ == "__main__":
    main()
