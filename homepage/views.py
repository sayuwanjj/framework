"""Главная страница и страница ошибки 404."""

from django.shortcuts import render

from db.database import get_connection


def index(request):
    """Главная страница: описание сервиса и статистика по статусам."""
    conn = get_connection()
    try:
        layouts_count = conn.execute(
            "SELECT COUNT(*) AS layouts_count FROM layouts"
        ).fetchone()["layouts_count"]
        statistics = conn.execute(
            """
            SELECT
                status,
                COUNT(*) AS layouts_count
            FROM layouts
            GROUP BY status
            ORDER BY layouts_count DESC, status
            """
        ).fetchall()
    finally:
        conn.close()

    context = {
        "layouts_count": layouts_count,
        "statistics": statistics,
    }
    return render(request, "homepage/index.html", context)


def page_not_found(request, exception):
    """Собственная страница ошибки 404 для всех приложений проекта."""
    return render(request, "404.html", status=404)
