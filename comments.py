"""Функции для работы с комментариями клиентов к макетам."""

from datetime import date


def add_comment(
    comments: list[dict],
    layout_id: int,
    author: str,
    text: str,
    comment_date: date,
    layout_version: int,
) -> dict:
    """Добавить комментарий клиента к макету.

    Вызывает ValueError, если текст комментария пустой.
    """
    if len(text.strip()) == 0:
        raise ValueError("Текст комментария не может быть пустым")
    comment_id = max((item["id"] for item in comments), default=0) + 1
    comment = {
        "id": comment_id,
        "layout_id": layout_id,
        "author": author,
        "text": text.strip(),
        "date": comment_date.isoformat(),
        "layout_version": layout_version,
    }
    comments.append(comment)
    return comment


def get_layout_comments(comments: list[dict], layout_id: int) -> list[dict]:
    """Вернуть комментарии, относящиеся к указанному макету."""
    return [item for item in comments if item["layout_id"] == layout_id]


def has_comments(comments: list[dict], layout_id: int) -> bool:
    """Проверить, есть ли у макета хотя бы один комментарий."""
    return len(get_layout_comments(comments, layout_id)) > 0


def count_comments_by_layout(comments: list[dict]) -> dict[int, int]:
    """Посчитать количество комментариев для каждого макета."""
    statistics: dict[int, int] = {}
    for comment in comments:
        layout_id = comment["layout_id"]
        statistics[layout_id] = statistics.get(layout_id, 0) + 1
    return statistics


def format_comment(comment: dict) -> str:
    """Сформировать строку комментария для вывода на экран."""
    return (
        f"[{comment['date']}] {comment['author']} "
        f"(версия {comment['layout_version']}): {comment['text']}"
    )
