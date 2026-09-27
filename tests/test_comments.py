"""Тесты функций работы с комментариями."""

from datetime import date

import pytest

from comments import add_comment, get_layout_comments, has_comments


def test_add_comment():
    comments = []
    add_comment(comments, 1, "Клиент", "Увеличить логотип",
                date(2026, 9, 13), 1)
    assert len(comments) == 1
    assert comments[0]["layout_id"] == 1


def test_empty_comment_raises_error():
    comments = []
    with pytest.raises(ValueError):
        add_comment(comments, 1, "Клиент", "   ", date(2026, 9, 13), 1)


def test_get_layout_comments():
    comments = []
    add_comment(comments, 1, "Клиент", "Первый", date(2026, 9, 13), 1)
    add_comment(comments, 2, "Клиент", "Второй", date(2026, 9, 13), 1)
    assert len(get_layout_comments(comments, 1)) == 1
    assert has_comments(comments, 3) is False
