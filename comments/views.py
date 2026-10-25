"""Страницы комментариев: данные получаются из базы SQLite."""

from django.shortcuts import render

from db.database import get_connection


def comments(request):
    """Страница /comments/: комментарии с макетом и автором (JOIN)."""
    conn = get_connection()
    try:
        comments_list = conn.execute(
            """
            SELECT
                comments.id,
                comments.text,
                comments.comment_date,
                comments.layout_version,
                layouts.title AS layout_title,
                clients.name AS author_name
            FROM comments
            JOIN layouts ON comments.layout_id = layouts.id
            JOIN clients ON comments.author_id = clients.id
            ORDER BY comments.comment_date DESC, comments.id
            """
        ).fetchall()
    finally:
        conn.close()

    context = {"comments": comments_list}
    return render(request, "comments/comment_list.html", context)


def comment_detail(request, comment_id):
    """Страница /comments/<id>/: карточка комментария."""
    conn = get_connection()
    try:
        comment = conn.execute(
            """
            SELECT
                comments.id,
                comments.text,
                comments.comment_date,
                comments.layout_version,
                layouts.id AS layout_id,
                layouts.title AS layout_title,
                clients.name AS author_name,
                clients.company AS author_company
            FROM comments
            JOIN layouts ON comments.layout_id = layouts.id
            JOIN clients ON comments.author_id = clients.id
            WHERE comments.id = ?
            """,
            [comment_id],
        ).fetchone()
    finally:
        conn.close()

    context = {"comment": comment}
    return render(
        request,
        "comments/comment_detail.html",
        context,
        status=404 if comment is None else 200,
    )
