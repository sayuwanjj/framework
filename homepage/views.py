"""Главная страница, общий HTML-каркас и страница ошибки 404."""

from django.http import HttpResponse

from models.layouts import count_by_status
from storage import load_clients, load_designers, load_layouts


def page(title, content):
    """Собрать HTML-документ с общим каркасом для всех страниц."""
    bootstrap = (
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3"
        "/dist/css/bootstrap.min.css"
    )
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <link rel="stylesheet" href="{bootstrap}">
</head>
<body>
    <nav class="nav bg-light border-bottom mb-4">
        <a class="nav-link" href="/">Главная</a>
        <a class="nav-link" href="/layouts/">Макеты</a>
        <a class="nav-link" href="/comments/">Комментарии</a>
    </nav>
    <main class="container">{content}</main>
</body>
</html>"""


def index(request):
    """Главная страница: описание сервиса, статистика и навигация."""
    designers = load_designers()
    clients = load_clients()
    layouts_list = load_layouts(designers, clients)

    items = ""
    for status, amount in count_by_status(layouts_list).items():
        items += f"""
        <li class="list-group-item d-flex justify-content-between">
            {status}
            <span class="badge bg-primary rounded-pill">{amount}</span>
        </li>"""

    content = f"""
    <h1 class="display-5">Сервис согласования макетов</h1>
    <p class="lead">
        Дизайнер отправляет макет клиенту, клиент оставляет комментарии
        и утверждает макет или отправляет его на доработку.
    </p>
    <h2 class="h5 mt-4">Макеты по статусам</h2>
    <ul class="list-group mb-4">{items}</ul>
    <a href="/layouts/" class="btn btn-primary me-2">Макеты</a>
    <a href="/comments/" class="btn btn-secondary">Комментарии</a>
    """
    return HttpResponse(page("Сервис согласования макетов", content))


def page_not_found(request, exception):
    """Собственная страница ошибки 404 для всех приложений проекта."""
    content = """
    <h1 class="text-danger">404 - страница не найдена</h1>
    <p>Проверьте адрес или вернитесь на главную.</p>
    <a href="/" class="btn btn-primary">На главную</a>
    """
    return HttpResponse(
        page("404 - страница не найдена", content),
        status=404,
    )
