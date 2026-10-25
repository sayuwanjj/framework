"""Тесты слоя базы данных SQLite (ПР7).

Каждый тест работает с временной базой в каталоге tmp_path,
поэтому рабочая база data/layout_service.sqlite не изменяется.
"""

import sqlite3

import pytest

from db import import_json
from db.database import get_connection


@pytest.fixture
def db_path(tmp_path):
    """Создать временную базу и перенести в неё данные из JSON."""
    path = tmp_path / "test.sqlite"
    import_json.main(path)
    return path


@pytest.fixture
def conn(db_path):
    """Открыть соединение с временной базой."""
    connection = get_connection(db_path)
    yield connection
    connection.close()


def count_rows(conn, table_query):
    """Вернуть количество строк по готовому запросу COUNT(*)."""
    return conn.execute(table_query).fetchone()[0]


def test_import_copies_all_records(conn):
    assert count_rows(conn, "SELECT COUNT(*) FROM designers") == len(
        import_json.load_json(import_json.DESIGNERS_FILE)
    )
    assert count_rows(conn, "SELECT COUNT(*) FROM clients") == len(
        import_json.load_json(import_json.CLIENTS_FILE)
    )
    assert count_rows(conn, "SELECT COUNT(*) FROM layouts") == len(
        import_json.load_json(import_json.LAYOUTS_FILE)
    )
    assert count_rows(conn, "SELECT COUNT(*) FROM comments") == len(
        import_json.load_json(import_json.COMMENTS_FILE)
    )


def test_import_can_be_repeated(db_path):
    import_json.main(db_path)
    conn = get_connection(db_path)
    try:
        layouts_count = count_rows(conn, "SELECT COUNT(*) FROM layouts")
    finally:
        conn.close()
    expected = import_json.load_json(import_json.LAYOUTS_FILE)
    assert layouts_count == len(expected)


def test_row_fields_available_by_name(conn):
    row = conn.execute(
        "SELECT title, status FROM layouts WHERE id = ?",
        [1],
    ).fetchone()
    assert row["title"] == "Главная страница интернет-магазина"
    assert row["status"] == "На доработке"


def test_foreign_key_is_checked(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """
            INSERT INTO layouts (
                title, designer_id, client_id, sent_date, approval_days
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            ["Макет без дизайнера", 999, 1, "2026-10-01", 5],
        )


def test_join_returns_related_names(conn):
    row = conn.execute(
        """
        SELECT designers.name AS designer_name, clients.name AS client_name
        FROM layouts
        JOIN designers ON layouts.designer_id = designers.id
        JOIN clients ON layouts.client_id = clients.id
        WHERE layouts.id = ?
        """,
        [3],
    ).fetchone()
    assert row["designer_name"] == "Смирнов Илья"
    assert row["client_name"] == "Кузнецов Олег"


def test_group_by_and_having(conn):
    rows = conn.execute(
        """
        SELECT layouts.id, COUNT(comments.id) AS comments_count
        FROM layouts
        JOIN comments ON layouts.id = comments.layout_id
        GROUP BY layouts.id
        HAVING COUNT(comments.id) >= ?
        """,
        [2],
    ).fetchall()
    assert [(row["id"], row["comments_count"]) for row in rows] == [(1, 2)]


def test_parameter_is_not_part_of_sql(conn):
    rows = conn.execute(
        "SELECT id FROM layouts WHERE title LIKE '%' || ? || '%'",
        ["' OR 1=1 --"],
    ).fetchall()
    assert rows == []
