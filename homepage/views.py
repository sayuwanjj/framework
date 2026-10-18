"""Главная страница и страница ошибки 404."""

from django.shortcuts import render

from models.layouts import count_by_status
from storage import load_clients, load_designers, load_layouts


def index(request):
    """Главная страница: описание сервиса и статистика по статусам."""
    designers = load_designers()
    clients = load_clients()
    layouts_list = load_layouts(designers, clients)

    context = {
        "layouts": layouts_list,
        "statistics": count_by_status(layouts_list),
    }
    return render(request, "homepage/index.html", context)


def page_not_found(request, exception):
    """Собственная страница ошибки 404 для всех приложений проекта."""
    return render(request, "404.html", status=404)
