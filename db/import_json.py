"""Перенос данных проекта из JSON-файлов в базу данных SQLite.

Запуск из корня проекта:

    python -m db.import_json

Скрипт создаёт таблицы (если их ещё нет), очищает их и заново
заполняет данными из JSON, поэтому его можно запускать повторно.
"""

import json
from pathlib import Path

from db.database import BASE_DIR, DB_PATH, create_tables, get_connection

DESIGNERS_FILE = BASE_DIR / "data" / "designers.json"
CLIENTS_FILE = BASE_DIR / "data" / "clients.json"
LAYOUTS_FILE = BASE_DIR / "data" / "layouts.json"
COMMENTS_FILE = BASE_DIR / "data" / "comments.json"


def load_json(filename: Path) -> list[dict]:
    """Прочитать список записей из JSON-файла."""
    with open(filename, encoding="utf-8") as file:
        return json.load(file)


def clear_tables(conn) -> None:
    """Удалить старые записи: сначала зависимые таблицы, затем главные."""
    conn.execute("DELETE FROM comments")
    conn.execute("DELETE FROM layouts")
    conn.execute("DELETE FROM clients")
    conn.execute("DELETE FROM designers")


def import_designers(conn) -> int:
    """Перенести дизайнеров в таблицу designers."""
    designers = load_json(DESIGNERS_FILE)
    conn.executemany(
        """
        INSERT INTO designers (id, name, email)
        VALUES (?, ?, ?)
        """,
        [(item["id"], item["name"], item["email"]) for item in designers],
    )
    return len(designers)


def import_clients(conn) -> int:
    """Перенести клиентов в таблицу clients."""
    clients = load_json(CLIENTS_FILE)
    conn.executemany(
        """
        INSERT INTO clients (id, name, email, company)
        VALUES (?, ?, ?, ?)
        """,
        [
            (item["id"], item["name"], item["email"], item.get("company"))
            for item in clients
        ],
    )
    return len(clients)


def import_layouts(conn) -> int:
    """Перенести макеты в таблицу layouts."""
    layouts = load_json(LAYOUTS_FILE)
    conn.executemany(
        """
        INSERT INTO layouts (
            id, title, version, designer_id, client_id,
            sent_date, approval_days, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                item["id"],
                item["title"],
                item["version"],
                item["designer_id"],
                item["client_id"],
                item["sent_date"],
                int(item["approval_days"]),
                item["status"],
            )
            for item in layouts
        ],
    )
    return len(layouts)


def import_comments(conn) -> int:
    """Перенести комментарии в таблицу comments.

    Поле date из JSON сохраняется в столбец comment_date.
    """
    comments = load_json(COMMENTS_FILE)
    conn.executemany(
        """
        INSERT INTO comments (
            id, layout_id, author_id, text, comment_date, layout_version
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                item["id"],
                item["layout_id"],
                item["author_id"],
                item["text"],
                item["date"],
                item["layout_version"],
            )
            for item in comments
        ],
    )
    return len(comments)


def main(db_path: Path | str = DB_PATH) -> None:
    """Создать таблицы и перенести в них все данные из JSON.

    Порядок импорта важен: сначала таблицы, на которые ссылаются
    внешние ключи (designers, clients), затем layouts и comments.
    """
    conn = get_connection(db_path)
    try:
        create_tables(conn)
        clear_tables(conn)
        counts = {
            "designers": import_designers(conn),
            "clients": import_clients(conn),
            "layouts": import_layouts(conn),
            "comments": import_comments(conn),
        }
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print(f"База данных: {db_path}")
    for table, amount in counts.items():
        print(f"Таблица {table}: перенесено записей — {amount}")


if __name__ == "__main__":
    main()
