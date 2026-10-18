"""Страницы макетов: список макетов и карточка отдельного макета."""

from datetime import date

from django.shortcuts import render

from models.comments import get_layout_comments
from models.layouts import get_layout_by_id, sort_layouts
from storage import load_clients, load_comments, load_designers, load_layouts


def layouts(request):
    """Страница /layouts/: список макетов, отсортированный по сроку."""
    designers = load_designers()
    clients = load_clients()
    layouts_list = load_layouts(designers, clients)

    context = {
        "layouts": sort_layouts(layouts_list),
    }
    return render(request, "layouts/layout_list.html", context)


def layout_detail(request, layout_id):
    """Страница /layouts/<id>/: карточка макета и его комментарии."""
    designers = load_designers()
    clients = load_clients()
    layouts_list = load_layouts(designers, clients)

    layout = get_layout_by_id(layouts_list, layout_id)

    context = {"layout": layout}
    if layout is not None:
        comments_list = load_comments(layouts_list, clients)
        context["comments"] = get_layout_comments(comments_list, layout)
        context["days_left"] = layout.days_left(date.today())

    return render(
        request,
        "layouts/layout_detail.html",
        context,
        status=404 if layout is None else 200,
    )
