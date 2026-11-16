"""Страницы макетов: данные получаются через Django ORM."""

from datetime import date, datetime

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import (Avg, Case, CharField, Count, F, Max, Q, Value,
                              When)
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from comments.models import Comment
from layouts.forms import LayoutFilterForm, LayoutForm
from layouts.models import Layout
from participants.models import Designer

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


def with_names(queryset):
    """Добавить к макетам имена дизайнера и клиента (annotate + F)."""
    return queryset.annotate(
        designer_name=F("designer__name"),
        client_name=F("client__name"),
        status_label=Case(
            *[When(status=value, then=Value(label))
              for value, label in Layout.Status.choices],
            default=F("status"), output_field=CharField(),
        ),
    )


def parse_date(value: str) -> date | None:
    """Преобразовать строку ГГГГ-ММ-ДД в дату или вернуть None."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def layouts(request):
    """Страница /layouts/: фильтры, сортировка и постраничный вывод."""
    filter_form = LayoutFilterForm(request.GET if request.GET else None)
    sort = "deadline"
    layouts_data = Layout.objects.all()
    if filter_form.is_bound:
        if filter_form.is_valid():
            data = filter_form.cleaned_data
            if data["status"]:
                layouts_data = layouts_data.filter(status=data["status"])
            if data["designer"]:
                layouts_data = layouts_data.filter(designer=data["designer"])
            if data["client"]:
                layouts_data = layouts_data.filter(client=data["client"])
            if data["date"]:
                layouts_data = layouts_data.filter(sent_date=data["date"])
            if data["active_only"]:
                layouts_data = layouts_data.active()
            sort = data["sort"] or "deadline"
        else:
            layouts_data = layouts_data.none()

    layouts_data = (
        with_names(layouts_data)
        .order_by(SORT_FIELDS[sort], "pk")
        .values(
            "id",
            "slug",
            "status_label",
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
        "filter_form": filter_form,
        "sort": sort,

    }
    return render(request, "layouts/layout_list.html", context)


def layout_detail(request, layout_id=None, slug=None):
    """Страница /layouts/<id>/: карточка макета и его комментарии."""
    # select_related загружает дизайнера и клиента тем же запросом.
    layout = get_object_or_404(
        Layout.objects.select_related("designer", "client"),
        **({"slug": slug} if slug is not None else {"pk": layout_id}),
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
        "statuses": Layout.Status.choices,
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
        waiting_count=Count("id", filter=Q(
            status__in=[Layout.Status.REVIEW, Layout.Status.REVISION])),
        avg_days=Avg("approval_days"),
        max_version=Max("version"),
    )
    totals["comments_count"] = Comment.objects.count()

    # values() + annotate() — группировка по статусу (GROUP BY).
    by_status = (
        with_names(Layout.objects.all()).values("status", "status_label")
        .annotate(layouts_count=Count("id"))
        .order_by("-layouts_count", "status")
    )

    # Запрос начинается с Designer, поэтому дизайнеры без макетов
    # тоже попадают в результат (аналог LEFT JOIN) со значением 0.
    by_designer = Designer.objects.annotate(
        layouts_count=Count("layouts"),
        waiting_count=Count(
            "layouts",
            filter=Q(layouts__status__in=[
                     Layout.Status.REVIEW, Layout.Status.REVISION]),
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


def save_layout_form(form):
    """Перехватить конфликт уникальности при одновременной отправке."""
    try:
        with transaction.atomic():
            return form.save()
    except IntegrityError:
        form.add_error(
            None, "Сохранение не выполнено: активная заявка уже существует.")
        return None


@require_http_methods(["GET", "POST"])
def layout_create(request):
    """GET показывает форму; успешный POST создаёт макет и перенаправляет."""
    if request.method == "POST":
        form = LayoutForm(request.POST, request.FILES)
        if form.is_valid():
            layout = save_layout_form(form)
            if layout is not None:
                messages.success(
                    request, "Макет создан и отправлен на согласование.")
                return redirect(layout)
    else:
        form = LayoutForm()
    return render(request, "layouts/layout_form.html", {"form": form})


@require_http_methods(["GET", "POST"])
def layout_update(request, layout_id):
    """Изменить существующую активную заявку, сохранив её id и slug."""
    layout = get_object_or_404(Layout.objects.active(), pk=layout_id)
    if request.method == "POST":
        form = LayoutForm(request.POST, request.FILES, instance=layout)
        if form.is_valid():
            saved = save_layout_form(form)
            if saved is not None:
                messages.success(request, "Изменения макета сохранены.")
                return redirect(saved)
    else:
        form = LayoutForm(instance=layout)
    return render(request, "layouts/layout_form.html", {
        "form": form, "layout": layout,
    })


@require_POST
def layout_cancel(request, layout_id):
    """Отмена доступна только через защищённый POST; история сохраняется."""
    layout = get_object_or_404(Layout.objects.active(), pk=layout_id)
    layout.cancel()
    messages.success(
        request, "Согласование отменено. Запись сохранена в истории.")
    return redirect(layout)
