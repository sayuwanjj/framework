"""Мини-консоль для выполнения SQL-запросов к базе проекта.

Замена SQLite CLI, если программа sqlite3 не установлена в системе.
Запуск из корня проекта:

    python -m db.shell

Запрос можно вводить в несколько строк, он выполняется после ";".
Команда .tables выводит список таблиц, .exit завершает работу.
"""

import sqlite3

from db.database import DB_PATH, get_connection

TABLES_QUERY = """
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    ORDER BY name
"""


def print_rows(cursor: sqlite3.Cursor) -> None:
    """Вывести результат запроса в виде строк, разделённых «|»."""
    if cursor.description is None:
        print(f"Готово, изменено строк: {cursor.rowcount}")
        return
    print(" | ".join(column[0] for column in cursor.description))
    rows = cursor.fetchall()
    for row in rows:
        print(" | ".join(str(value) for value in row))
    print(f"Строк в результате: {len(rows)}")


def main() -> None:
    """Читать SQL-запросы с клавиатуры и выполнять их."""
    conn = get_connection()
    print(f"База данных: {DB_PATH}")
    print("Введите SQL-запрос, завершив его «;». Выход — .exit")
    buffer: list[str] = []
    try:
        while True:
            line = input("sql> " if not buffer else "...> ")
            command = line.strip()
            if not buffer and command == ".exit":
                break
            if not buffer and command == ".tables":
                print_rows(conn.execute(TABLES_QUERY))
                continue
            buffer.append(line)
            if not command.endswith(";"):
                continue
            query = "\n".join(buffer)
            buffer.clear()
            try:
                print_rows(conn.execute(query))
                conn.commit()
            except sqlite3.Error as error:
                print(f"Ошибка SQL: {error}")
    except (EOFError, KeyboardInterrupt):
        print()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
