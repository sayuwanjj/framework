"""Страницы макетов: данные получаются из базы SQLite SQL-запросами."""

from datetime import date

from django.shortcuts import render

from db.database import get_connection

STATUSES = ["На согласовании", "На доработке", "Утверждён"]


def layouts(request):
    """Страница /layouts/: макеты с именами дизайнера и клиента (JOIN)."""
    conn = get_connection()
    try:
        layouts_list = conn.execute(
            """
            SELECT
                layouts.id,
                layouts.title,
                layouts.version,
                layouts.status,
                date(
                    layouts.sent_date, '+' || layouts.approval_days || ' days'
                ) AS deadline,
                designers.name AS designer_name,
                clients.name AS client_name
            FROM layouts
            JOIN designers ON layouts.designer_id = designers.id
            JOIN clients ON layouts.client_id = clients.id
            ORDER BY deadline
            """
        ).fetchall()
    finally:
        conn.close()

    context = {"layouts": layouts_list}
    return render(request, "layouts/layout_list.html", context)


def layout_detail(request, layout_id):
    """Страница /layouts/<id>/: карточка макета и его комментарии."""
    conn = get_connection()
    try:
        layout = conn.execute(
            """
            SELECT
                layouts.id,
                layouts.title,
                layouts.version,
                layouts.status,
                layouts.sent_date,
                date(
                    layouts.sent_date, '+' || layouts.approval_days || ' days'
                ) AS deadline,
                designers.name AS designer_name,
                clients.name AS client_name,
                clients.company AS client_company
            FROM layouts
            JOIN designers ON layouts.designer_id = designers.id
            JOIN clients ON layouts.client_id = clients.id
            WHERE layouts.id = ?
            """,
            [layout_id],
        ).fetchone()

        comments = []
        if layout is not None:
            comments = conn.execute(
                """
                SELECT
                    comments.id,
                    comments.text,
                    comments.comment_date,
                    comments.layout_version,
                    clients.name AS author_name
                FROM comments
                JOIN clients ON comments.author_id = clients.id
                WHERE comments.layout_id = ?
                ORDER BY comments.comment_date, comments.id
                """,
                [layout_id],
            ).fetchall()
    finally:
        conn.close()

    context = {"layout": layout, "comments": comments}
    if layout is not None:
        deadline = date.fromisoformat(layout["deadline"])
        context["days_left"] = (deadline - date.today()).days

    return render(
        request,
        "layouts/layout_detail.html",
        context,
        status=404 if layout is None else 200,
    )


def search(request):
    """Страница /layouts/search/: поиск по названию и статусу.

    Значения из формы передаются в запрос параметрами ?,
    а не подставляются в текст SQL.
    """
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    searched = "q" in request.GET or "status" in request.GET
    results = []

    if searched:
        conn = get_connection()
        try:
            results = conn.execute(
                """
                SELECT
                    layouts.id,
                    layouts.title,
                    layouts.version,
                    layouts.status,
                    date(
                        layouts.sent_date,
                        '+' || layouts.approval_days || ' days'
                    ) AS deadline,
                    designers.name AS designer_name,
                    clients.name AS client_name
                FROM layouts
                JOIN designers ON layouts.designer_id = designers.id
                JOIN clients ON layouts.client_id = clients.id
                WHERE layouts.title LIKE '%' || ? || '%'
                    AND (? = '' OR layouts.status = ?)
                ORDER BY layouts.title
                """,
                [query, status, status],
            ).fetchall()
        finally:
            conn.close()

    context = {
        "query": query,
        "status": status,
        "statuses": STATUSES,
        "searched": searched,
        "layouts": results,
    }
    return render(request, "layouts/search.html", context)


def overdue(request):
    """Страница /layouts/overdue/: макеты с истёкшим сроком на дату.

    Отбираются неутверждённые макеты, у которых срок согласования
    (дата отправки + approval_days) раньше выбранной даты.
    """
    check_date = request.GET.get("date", "")
    results = []

    if check_date:
        conn = get_connection()
        try:
            results = conn.execute(
                """
                SELECT
                    layouts.id,
                    layouts.title,
                    layouts.version,
                    layouts.status,
                    date(
                        layouts.sent_date,
                        '+' || layouts.approval_days || ' days'
                    ) AS deadline,
                    designers.name AS designer_name,
                    clients.name AS client_name
                FROM layouts
                JOIN designers ON layouts.designer_id = designers.id
                JOIN clients ON layouts.client_id = clients.id
                WHERE layouts.status != 'Утверждён'
                    AND date(
                        layouts.sent_date,
                        '+' || layouts.approval_days || ' days'
                    ) < ?
                ORDER BY deadline
                """,
                [check_date],
            ).fetchall()
        finally:
            conn.close()

    context = {"check_date": check_date, "layouts": results}
    return render(request, "layouts/overdue.html", context)


def statistics(request):
    """Страница /layouts/statistics/: агрегатные запросы и GROUP BY."""
    try:
        min_comments = int(request.GET.get("min", 2))
    except ValueError:
        min_comments = 2

    conn = get_connection()
    try:
        totals = conn.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM layouts) AS layouts_count,
                (SELECT COUNT(*) FROM comments) AS comments_count,
                (
                    SELECT COUNT(*)
                    FROM layouts
                    WHERE status != 'Утверждён'
                ) AS waiting_count
            """
        ).fetchone()

        by_status = conn.execute(
            """
            SELECT
                status,
                COUNT(*) AS layouts_count
            FROM layouts
            GROUP BY status
            ORDER BY layouts_count DESC, status
            """
        ).fetchall()

        by_designer = conn.execute(
            """
            SELECT
                designers.name AS designer_name,
                COUNT(layouts.id) AS layouts_count
            FROM designers
            LEFT JOIN layouts ON designers.id = layouts.designer_id
            GROUP BY designers.id, designers.name
            ORDER BY layouts_count DESC, designer_name
            """
        ).fetchall()

        by_layout = conn.execute(
            """
            SELECT
                layouts.id,
                layouts.title,
                COUNT(comments.id) AS comments_count
            FROM layouts
            LEFT JOIN comments ON layouts.id = comments.layout_id
            GROUP BY layouts.id, layouts.title
            ORDER BY comments_count DESC, layouts.title
            """
        ).fetchall()

        discussed = conn.execute(
            """
            SELECT
                layouts.id,
                layouts.title,
                COUNT(comments.id) AS comments_count
            FROM layouts
            JOIN comments ON layouts.id = comments.layout_id
            GROUP BY layouts.id, layouts.title
            HAVING COUNT(comments.id) >= ?
            ORDER BY comments_count DESC
            """,
            [min_comments],
        ).fetchall()

        without_comments = conn.execute(
            """
            SELECT
                id,
                title,
                status
            FROM layouts
            WHERE id NOT IN (
                SELECT layout_id
                FROM comments
            )
            ORDER BY title
            """
        ).fetchall()
    finally:
        conn.close()

    context = {
        "totals": totals,
        "by_status": by_status,
        "by_designer": by_designer,
        "by_layout": by_layout,
        "min_comments": min_comments,
        "discussed": discussed,
        "without_comments": without_comments,
    }
    return render(request, "layouts/statistics.html", context)
