"""Тесты функций работы с макетами."""

from datetime import date

from layouts import (
    STATUS_APPROVED,
    STATUS_REVIEW,
    add_layout,
    approve_layout,
    count_by_status,
    find_layout,
    send_to_revision,
    sort_layouts,
)


def test_add_layout():
    layouts = []
    add_layout(
        layouts,
        "Главная страница",
        "Грязнова Арина",
        "ООО «Ромашка»",
        date(2026, 9, 10),
        5,
    )
    assert len(layouts) == 1
    assert layouts[0]["deadline"] == "2026-09-15"
    assert layouts[0]["status"] == STATUS_REVIEW


def test_find_layout():
    layouts = []
    add_layout(
        layouts, "Карточка товара", "Дизайнер", "Клиент",
        date(2026, 9, 10), 5,
    )
    assert find_layout(layouts, "карточка")
    assert find_layout(layouts, "баннер") == []


def test_sort_layouts():
    layouts = []
    add_layout(
        layouts, "Поздний макет", "Дизайнер", "Клиент",
        date(2026, 9, 20), 5,
    )
    add_layout(
        layouts, "Ранний макет", "Дизайнер", "Клиент",
        date(2026, 9, 1), 5,
    )
    assert sort_layouts(layouts)[0]["title"] == "Ранний макет"


def test_send_to_revision_increases_version():
    layouts = []
    layout = add_layout(
        layouts, "Баннер", "Дизайнер", "Клиент",
        date(2026, 9, 10), 5,
    )
    send_to_revision(layouts, layout["id"])
    assert layouts[0]["version"] == 2


def test_count_by_status():
    layouts = []
    layout = add_layout(
        layouts, "Баннер", "Дизайнер", "Клиент",
        date(2026, 9, 10), 5,
    )
    approve_layout(layouts, layout["id"])
    assert count_by_status(layouts)[STATUS_APPROVED] == 1
