"""Тесты класса Comment и функций работы с комментариями."""

from datetime import date

import pytest

from models import Client, Comment, Designer, Layout
from models.comments import add_comment, get_layout_comments, has_comments

DESIGNER = Designer(1, "Грязнова Арина", "arina@example.com")
CLIENT = Client(1, "Иванов Пётр", "p@example.com", "ООО «Ромашка»")


def make_layout(layout_id=1):
    return Layout(
        layout_id,
        "Главная страница",
        DESIGNER,
        CLIENT,
        date(2026, 9, 10),
        5,
    )


def test_comment_creation():
    layout = make_layout()
    comment = Comment(
        1, layout, CLIENT, "Увеличить логотип", date(2026, 9, 13), 1
    )
    assert comment.layout is layout
    assert comment.author is CLIENT
    assert "Увеличить логотип" in str(comment)


def test_is_valid_text():
    assert Comment.is_valid_text("Текст")
    assert not Comment.is_valid_text("   ")


def test_empty_comment_raises_error():
    layout = make_layout()
    with pytest.raises(ValueError):
        add_comment([], layout, CLIENT, "   ", date(2026, 9, 13))


def test_add_comment_uses_current_version():
    layout = make_layout()
    layout.send_to_revision()
    comments = []
    comment = add_comment(
        comments, layout, CLIENT, "Поправить отступы", date(2026, 9, 13)
    )
    assert comment.layout_version == 2
    assert len(comments) == 1


def test_get_layout_comments():
    first = make_layout(1)
    second = make_layout(2)
    comments = []
    add_comment(comments, first, CLIENT, "Первый", date(2026, 9, 13))
    add_comment(comments, second, CLIENT, "Второй", date(2026, 9, 13))
    assert len(get_layout_comments(comments, first)) == 1
    assert has_comments(comments, second) is True
