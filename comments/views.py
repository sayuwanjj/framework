"""Страницы комментариев: список и карточка отдельного комментария."""

from django.shortcuts import render

from models.comments import get_comment_by_id
from storage import load_clients, load_comments, load_designers, load_layouts


def load_all_comments():
    """Загрузить участников, макеты и связанные с ними комментарии."""
    designers = load_designers()
    clients = load_clients()
    layouts_list = load_layouts(designers, clients)
    return load_comments(layouts_list, clients)


def comments(request):
    """Страница /comments/: все комментарии клиентов к макетам."""
    context = {
        "comments": load_all_comments(),
    }
    return render(request, "comments/comment_list.html", context)


def comment_detail(request, comment_id):
    """Страница /comments/<id>/: карточка комментария."""
    comment = get_comment_by_id(load_all_comments(), comment_id)

    context = {
        "comment": comment,
    }
    return render(
        request,
        "comments/comment_detail.html",
        context,
        status=404 if comment is None else 200,
    )
