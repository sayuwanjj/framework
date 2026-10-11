"""Страницы макетов: список макетов и карточка отдельного макета."""

from datetime import date

from django.http import HttpResponse

from homepage.views import page
from models import Layout
from models.comments import get_layout_comments
from models.layouts import get_layout_by_id, sort_layouts
from storage import load_clients, load_comments, load_designers, load_layouts

STATUS_BADGES = {
    Layout.STATUS_REVIEW: "bg-warning text-dark",
    Layout.STATUS_REVISION: "bg-secondary",
    Layout.STATUS_APPROVED: "bg-success",
}
DATE_FORMAT = "%d.%m.%Y"


def get_deadline_text(layout, today):
    """Сформировать текст о сроке согласования макета."""
    if layout.is_approved:
        return "макет утверждён"
    days = layout.days_left(today)
    if days < 0:
        return f"срок истёк {-days} дн. назад"
    return f"осталось {days} дн."


def layouts(request):
    """Страница /layouts/: список макетов, отсортированный по сроку."""
    designers = load_designers()
    clients = load_clients()
    layouts_list = load_layouts(designers, clients)

    items = ""
    for layout in sort_layouts(layouts_list):
        badge = STATUS_BADGES.get(layout.status, "bg-secondary")
        items += f"""
        <li class="list-group-item d-flex justify-content-between">
            <a href="/layouts/{layout.id}/">
                {layout.title} (версия {layout.version})
            </a>
            <span class="badge {badge}">{layout.status}</span>
        </li>"""

    content = f"""
    <h1>Макеты</h1>
    <ul class="list-group">{items}</ul>
    """
    return HttpResponse(page("Макеты", content))


def layout_detail(request, layout_id):
    """Страница /layouts/<id>/: карточка макета и его комментарии."""
    designers = load_designers()
    clients = load_clients()
    layouts_list = load_layouts(designers, clients)

    layout = get_layout_by_id(layouts_list, layout_id)

    if layout is None:
        content = """
        <h1 class="text-danger">Макет не найден</h1>
        <a href="/layouts/" class="btn btn-outline-secondary">
            ← к списку макетов
        </a>
        """
        return HttpResponse(
            page("Макет не найден", content),
            status=404,
        )

    comments_list = load_comments(layouts_list, clients)
    layout_comments = get_layout_comments(comments_list, layout)
    badge = STATUS_BADGES.get(layout.status, "bg-secondary")
    deadline_text = get_deadline_text(layout, date.today())

    comment_items = ""
    for comment in layout_comments:
        comment_items += f"""
        <li class="list-group-item">
            <a href="/comments/{comment.id}/">{comment.text}</a>
            <small class="text-muted">
                ({comment.date.strftime(DATE_FORMAT)},
                версия {comment.layout_version})
            </small>
        </li>"""
    if not comment_items:
        comment_items = '<li class="list-group-item">Комментариев нет</li>'

    content = f"""
    <div class="card mb-4">
        <div class="card-body">
            <h5 class="card-title">{layout.title}</h5>
            <p class="card-text"><strong>ID:</strong> {layout.id}</p>
            <p class="card-text">
                <strong>Версия:</strong> {layout.version}
            </p>
            <p class="card-text">
                <strong>Статус:</strong>
                <span class="badge {badge}">{layout.status}</span>
            </p>
            <p class="card-text">
                <strong>Дизайнер:</strong> {layout.designer.name}
            </p>
            <p class="card-text">
                <strong>Клиент:</strong> {layout.client.name},
                {layout.client.company}
            </p>
            <p class="card-text">
                <strong>Отправлен:</strong>
                {layout.sent_date.strftime(DATE_FORMAT)}
            </p>
            <p class="card-text">
                <strong>Срок согласования:</strong>
                {layout.deadline.strftime(DATE_FORMAT)} ({deadline_text})
            </p>
            <a href="/layouts/" class="btn btn-outline-secondary">
                ← к списку макетов
            </a>
        </div>
    </div>
    <h2 class="h4">Комментарии клиента</h2>
    <ul class="list-group">{comment_items}</ul>
    """
    return HttpResponse(
        page(layout.title, content),
        status=200,
    )
