"""Страницы комментариев: список и карточка отдельного комментария."""

from django.http import HttpResponse

from homepage.views import page
from models.comments import get_comment_by_id
from storage import load_clients, load_comments, load_designers, load_layouts

DATE_FORMAT = "%d.%m.%Y"


def load_all_comments():
    """Загрузить участников, макеты и связанные с ними комментарии."""
    designers = load_designers()
    clients = load_clients()
    layouts_list = load_layouts(designers, clients)
    return load_comments(layouts_list, clients)


def comments(request):
    """Страница /comments/: все комментарии клиентов к макетам."""
    items = ""
    for comment in load_all_comments():
        items += f"""
        <li class="list-group-item d-flex justify-content-between">
            <a href="/comments/{comment.id}/">
                {comment.layout.title}: {comment.text}
            </a>
            <span class="badge bg-info text-dark">
                {comment.date.strftime(DATE_FORMAT)}
            </span>
        </li>"""

    content = f"""
    <h1>Комментарии</h1>
    <ul class="list-group">{items}</ul>
    """
    return HttpResponse(page("Комментарии", content))


def comment_detail(request, comment_id):
    """Страница /comments/<id>/: карточка комментария."""
    comment = get_comment_by_id(load_all_comments(), comment_id)

    if comment is None:
        content = """
        <h1 class="text-danger">Комментарий не найден</h1>
        <a href="/comments/" class="btn btn-outline-secondary">
            ← к списку комментариев
        </a>
        """
        return HttpResponse(
            page("Комментарий не найден", content),
            status=404,
        )

    content = f"""
    <div class="card">
        <div class="card-body">
            <h5 class="card-title">Комментарий №{comment.id}</h5>
            <p class="card-text">
                <strong>Макет:</strong>
                <a href="/layouts/{comment.layout.id}/">
                    {comment.layout.title}
                </a>
                (версия {comment.layout_version})
            </p>
            <p class="card-text">
                <strong>Автор:</strong> {comment.author.name},
                {comment.author.company}
            </p>
            <p class="card-text">
                <strong>Дата:</strong>
                {comment.date.strftime(DATE_FORMAT)}
            </p>
            <p class="card-text"><strong>Текст:</strong> {comment.text}</p>
            <a href="/comments/" class="btn btn-outline-secondary">
                ← к списку комментариев
            </a>
        </div>
    </div>
    """
    return HttpResponse(
        page(f"Комментарий №{comment.id}", content),
        status=200,
    )
