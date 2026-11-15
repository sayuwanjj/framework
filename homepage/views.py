"""Главная страница и страница ошибки 404."""

from django.db.models import Count
from django.shortcuts import render

from layouts.models import Layout


def index(request):
    """Главная страница: описание сервиса и статистика по статусам."""
    statistics = (
        Layout.objects.values("status")
        .annotate(layouts_count=Count("id"))
        .order_by("-layouts_count", "status")
    )
    statistics = list(statistics)
    for item in statistics:
        item["status"] = Layout.Status(item["status"]).label

    context = {
        "layouts_count": Layout.objects.count(),
        "statistics": statistics,
    }
    return render(request, "homepage/index.html", context)


def page_not_found(request, exception):
    """Собственная страница ошибки 404 для всех приложений проекта."""
    return render(request, "404.html", status=404)
