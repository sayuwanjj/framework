"""Страницы макетов: данные получаются через Django ORM."""

from datetime import date, datetime

from django.core.paginator import Paginator
from django.db.models import Avg, Count, F, Max, Q
from django.shortcuts import get_object_or_404, render

from comments.models import Comment
from layouts.models import Layout
from participants.models import Client, Designer

# Количество макетов на одной странице списка.
LAYOUTS_PER_PAGE = 2

# Разрешённые значения параметра sort и соответствующие поля модели.
# Значение из адреса никогда не передаётся в order_by() напрямую.
SORT_FIELDS = {
    "deadline": "deadline",
    "sent": "-sent_date",
    "title": "title",
    "client": "client__name",
    "designer": "designer__name",
}
SORT_CHOICES = [
    ("deadline", "сроку согласования"),
    ("sent", "дате отправки (сначала новые)"),
    ("title", "названию"),
    ("client", "клиенту"),
    ("designer", "дизайнеру"),
]


def with_names(queryset):
    """Добавить к макетам имена дизайнера и клиента (annotate + F)."""
    return queryset.annotate(
        designer_name=F("designer__name"),
        client_name=F("client__name"),
    )


def parse_date(value: str) -> date | None:
    """Преобразовать строку ГГГГ-ММ-ДД в дату или вернуть None."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def layouts(request):
    """Страница /layouts/: фильтры, сортировка и постраничный вывод."""
    status = request.GET.get("status", "").strip()
    designer_id = request.GET.get("designer", "").strip()
    client_id = request.GET.get("client", "").strip()
    sort = request.GET.get("sort", "deadline")
    if sort not in SORT_FIELDS:
        sort = "deadline"

    layouts_data = Layout.objects.all()

    # Каждый filter() добавляет условие «И» и сужает выборку.
    if status in Layout.STATUSES:
        layouts_data = layouts_data.filter(status=status)
    if designer_id.isdigit():
        layouts_data = layouts_data.filter(designer_id=int(designer_id))
    if client_id.isdigit():
        layouts_data = layouts_data.filter(client_id=int(client_id))

    layouts_data = (
        with_names(layouts_data)
        .order_by(SORT_FIELDS[sort], "pk")
        .values(
            "id",
            "title",
            "version",
            "status",
            "deadline",
            "designer_name",
            "client_name",
        )
    )

    paginator = Paginator(layouts_data, LAYOUTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "layouts": page_obj,
        "page_obj": page_obj,
        "total": paginator.count,
        "statuses": Layout.STATUSES,
        "designers": Designer.objects.order_by("name"),
        "clients": Client.objects.order_by("name"),
        "selected_status": status,
        "selected_designer": designer_id,
        "selected_client": client_id,
        "sort": sort,
        "sort_choices": SORT_CHOICES,
    }
    return render(request, "layouts/layout_list.html", context)


def layout_detail(request, layout_id):
    """Страница /layouts/<id>/: карточка макета и его комментарии."""
    # select_related загружает дизайнера и клиента тем же запросом.
    layout = get_object_or_404(
        Layout.objects.select_related("designer", "client"),
        pk=layout_id,
    )
    # Обратная связь: комментарии макета через related_name="comments".
    comments = layout.comments.select_related("author")

    context = {
        "layout": layout,
        "comments": comments,
        "days_left": layout.days_left(date.today()),
    }
    return render(request, "layouts/layout_detail.html", context)


def search(request):
    """Страница /layouts/search/: поиск по нескольким полям и статусу."""
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    searched = "q" in request.GET or "status" in request.GET
    results = Layout.objects.none()

    if searched:
        results = Layout.objects.all()
        if query:
            # Q-объекты, соединённые «|», дают условие «ИЛИ».
            results = results.filter(
                Q(title__icontains=query)
                | Q(designer__name__icontains=query)
                | Q(client__name__icontains=query)
                | Q(client__company__icontains=query)
            )
        if status in Layout.STATUSES:
            results = results.filter(status=status)
        results = with_names(results).order_by("title")

    context = {
        "query": query,
        "status": status,
        "statuses": Layout.STATUSES,
        "searched": searched,
        "layouts": results,
    }
    return render(request, "layouts/search.html", context)


def overdue(request):
    """Страница /layouts/overdue/: макеты с истёкшим сроком на дату."""
    check_date = request.GET.get("date", "").strip()
    results = Layout.objects.none()
    error = None

    if check_date:
        selected_date = parse_date(check_date)
        if selected_date is None:
            error = "Укажите корректную дату в формате ГГГГ-ММ-ДД."
        else:
            results = with_names(
                Layout.objects.overdue(selected_date)
            ).order_by("deadline")

    context = {
        "check_date": check_date,
        "error": error,
        "layouts": results,
    }
    return render(request, "layouts/overdue.html", context)


def statistics(request):
    """Страница /layouts/statistics/: aggregate() и annotate()."""
    min_value = request.GET.get("min", "2")
    min_comments = int(min_value) if min_value.isdigit() else 2

    # aggregate() возвращает словарь с итоговыми показателями.
    totals = Layout.objects.aggregate(
        layouts_count=Count("id"),
        waiting_count=Count("id", filter=~Q(status=Layout.STATUS_APPROVED)),
        avg_days=Avg("approval_days"),
        max_version=Max("version"),
    )
    totals["comments_count"] = Comment.objects.count()

    # values() + annotate() — группировка по статусу (GROUP BY).
    by_status = (
        Layout.objects.values("status")
        .annotate(layouts_count=Count("id"))
        .order_by("-layouts_count", "status")
    )

    # Запрос начинается с Designer, поэтому дизайнеры без макетов
    # тоже попадают в результат (аналог LEFT JOIN) со значением 0.
    by_designer = Designer.objects.annotate(
        layouts_count=Count("layouts"),
        waiting_count=Count(
            "layouts",
            filter=~Q(layouts__status=Layout.STATUS_APPROVED),
        ),
    ).order_by("-layouts_count", "name")

    by_layout = Layout.objects.annotate(
        comments_count=Count("comments"),
    ).order_by("-comments_count", "title")

    # Фильтр по аннотированному полю — аналог HAVING.
    discussed = by_layout.filter(comments_count__gte=min_comments)

    without_comments = Layout.objects.filter(
        comments__isnull=True,
    ).order_by("title")

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
