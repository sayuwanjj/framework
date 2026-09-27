"""Функции для работы с макетами сервиса согласования.

Модуль содержит структуру данных макета, поиск, фильтрацию,
сортировку, смену статуса и статистику по макетам.
"""

from datetime import date, timedelta

STATUS_REVIEW = "На согласовании"
STATUS_REVISION = "На доработке"
STATUS_APPROVED = "Утверждён"


def add_layout(
    layouts: list[dict],
    title: str,
    designer: str,
    client: str,
    sent_date: date,
    approval_days: int,
) -> dict:
    """Добавить макет в список layouts.

    Формирует идентификатор макета, рассчитывает срок согласования
    и возвращает созданный макет.
    """
    layout_id = max((item["id"] for item in layouts), default=0) + 1
    deadline = sent_date + timedelta(days=int(approval_days))
    layout = {
        "id": layout_id,
        "title": title,
        "version": 1,
        "designer": designer,
        "client": client,
        "sent_date": sent_date.isoformat(),
        "deadline": deadline.isoformat(),
        "status": STATUS_REVIEW,
    }
    layouts.append(layout)
    return layout


def find_layout(layouts: list[dict], query: str) -> list[dict]:
    """Найти макеты по подстроке названия без учёта регистра."""
    return [
        layout
        for layout in layouts
        if query.lower() in layout["title"].lower()
    ]


def get_layout_by_id(layouts: list[dict], layout_id: int) -> dict | None:
    """Вернуть макет по идентификатору или None, если он не найден."""
    for layout in layouts:
        if layout["id"] == layout_id:
            return layout
    return None


def filter_layouts_by_status(layouts: list[dict], status: str) -> list[dict]:
    """Отобрать макеты с указанным статусом.

    Отбор выполняется генератором: значения формируются по мере
    перебора списка макетов.
    """
    selected = (item for item in layouts if item["status"] == status)
    return list(selected)


def sort_layouts(layouts: list[dict]) -> list[dict]:
    """Отсортировать макеты по сроку согласования (lambda-функция)."""
    return sorted(layouts, key=lambda layout: layout["deadline"])


def approve_layout(layouts: list[dict], layout_id: int) -> dict:
    """Утвердить макет.

    Вызывает ValueError, если макет не найден или уже утверждён.
    """
    layout = get_layout_by_id(layouts, layout_id)
    if layout is None:
        raise ValueError(f"Макет с id={layout_id} не найден")
    if layout["status"] == STATUS_APPROVED:
        raise ValueError("Макет уже утверждён")
    layout["status"] = STATUS_APPROVED
    return layout


def send_to_revision(layouts: list[dict], layout_id: int) -> dict:
    """Отправить макет на доработку и создать следующую версию."""
    layout = get_layout_by_id(layouts, layout_id)
    if layout is None:
        raise ValueError(f"Макет с id={layout_id} не найден")
    if layout["status"] == STATUS_APPROVED:
        raise ValueError("Утверждённый макет не отправляется на доработку")
    layout["status"] = STATUS_REVISION
    layout["version"] += 1
    return layout


def count_by_status(layouts: list[dict]) -> dict[str, int]:
    """Посчитать количество макетов по каждому статусу."""
    statistics = {
        STATUS_REVIEW: 0,
        STATUS_REVISION: 0,
        STATUS_APPROVED: 0,
    }
    for layout in layouts:
        status = layout["status"]
        statistics[status] = statistics.get(status, 0) + 1
    return statistics


def register_layout(
    title: str,
    version: int,
    designer: str,
    client: str,
    sent_date: date,
    approval_days: int,
) -> date:
    """Вывести карточку макета и вернуть срок ответа клиента.

    Функция перенесена из ПР1 и используется при выводе сведений
    о зарегистрированном макете.
    """
    deadline = sent_date + timedelta(days=int(approval_days))
    print("Макет зарегистрирован на согласование")
    print("Название: " + title + " (версия " + str(version) + ")")
    print("Дизайнер: " + designer)
    print("Клиент: " + client)
    print(f"Отправлен: {sent_date}, срок согласования до {deadline}")
    return deadline


def get_approval_status(is_approved: bool, has_comments: bool) -> str:
    """Определить текстовый статус согласования макета (из ПР1)."""
    if is_approved:
        return STATUS_APPROVED
    elif has_comments:
        return STATUS_REVISION
    else:
        return STATUS_REVIEW


def days_left(deadline: date, today: date) -> int:
    """Вернуть число дней, оставшихся до окончания срока (из ПР1)."""
    return (deadline - today).days
