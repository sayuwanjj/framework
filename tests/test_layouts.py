"""Тесты класса Layout и функций работы с коллекцией макетов."""

from datetime import date

import pytest

from models import Client, Designer, Layout
from models.layouts import (add_layout, count_by_status,
                            filter_layouts_by_status, find_layout,
                            sort_layouts)

DESIGNER = Designer(1, "Грязнова Арина", "arina@example.com")
CLIENT = Client(1, "Иванов Пётр", "p@example.com", "ООО «Ромашка»")


def make_layout(title="Главная страница", sent_day=10, days=5):
    return Layout(
        1, title, DESIGNER, CLIENT, date(2026, 9, sent_day), days
    )


def test_layout_creation():
    layout = make_layout()
    assert layout.id == 1
    assert layout.title == "Главная страница"
    assert layout.designer is DESIGNER
    assert layout.client is CLIENT
    assert layout.version == 1
    assert layout.status == Layout.STATUS_REVIEW


def test_layout_deadline_and_days_left():
    layout = make_layout()
    assert layout.deadline == date(2026, 9, 15)
    assert layout.days_left(date(2026, 9, 13)) == 2


def test_layout_str():
    assert "версия 1" in str(make_layout())


def test_approve_layout():
    layout = make_layout()
    layout.approve()
    assert layout.is_approved
    with pytest.raises(ValueError):
        layout.approve()


def test_send_to_revision_increases_version():
    layout = make_layout()
    layout.send_to_revision()
    assert layout.version == 2
    assert layout.status == Layout.STATUS_REVISION


def test_approved_layout_is_not_revised():
    layout = make_layout()
    layout.approve()
    with pytest.raises(ValueError):
        layout.send_to_revision()


def test_add_find_sort_and_count():
    layouts = []
    add_layout(
        layouts, "Поздний макет", DESIGNER, CLIENT, date(2026, 9, 20), 5
    )
    second = add_layout(
        layouts, "Ранний баннер", DESIGNER, CLIENT, date(2026, 9, 1), 5
    )
    assert len(layouts) == 2
    assert find_layout(layouts, "баннер")
    assert sort_layouts(layouts)[0] is second
    second.approve()
    assert count_by_status(layouts)[Layout.STATUS_APPROVED] == 1
    selected = filter_layouts_by_status(layouts, Layout.STATUS_APPROVED)
    assert selected == [second]
