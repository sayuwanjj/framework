"""Комментарий клиента к макету и операции над коллекцией."""

from datetime import date

from .layouts import Layout
from .participants import Client


class Comment:
    """Замечание клиента к конкретной версии макета."""

    def __init__(
        self,
        comment_id: int,
        layout: Layout,
        author: Client,
        text: str,
        comment_date: date,
        layout_version: int,
    ) -> None:
        """Создать комментарий и сохранить данные в атрибутах."""
        self.id = comment_id
        self.layout = layout
        self.author = author
        self.text = text
        self.date = comment_date
        self.layout_version = layout_version

    @staticmethod
    def is_valid_text(text: str) -> bool:
        """Проверить, что текст комментария не пустой."""
        return len(text.strip()) > 0

    @classmethod
    def from_data(
        cls,
        data: dict,
        layout: Layout,
        author: Client,
    ) -> "Comment":
        """Создать комментарий из данных JSON и найденных объектов."""
        return cls(
            comment_id=data["id"],
            layout=layout,
            author=author,
            text=data["text"],
            comment_date=date.fromisoformat(data["date"]),
            layout_version=data["layout_version"],
        )

    def to_data(self) -> dict:
        """Преобразовать комментарий в данные для сохранения в JSON."""
        return {
            "id": self.id,
            "layout_id": self.layout.id,
            "author_id": self.author.id,
            "text": self.text,
            "date": self.date.isoformat(),
            "layout_version": self.layout_version,
        }

    def __str__(self) -> str:
        """Строковое представление комментария."""
        return (
            f"[{self.date}] {self.author.name} "
            f"(версия {self.layout_version}): {self.text}"
        )


def add_comment(
    comments: list[Comment],
    layout: Layout,
    author: Client,
    text: str,
    comment_date: date,
) -> Comment:
    """Добавить комментарий клиента к макету.

    Вызывает ValueError, если текст комментария пустой.
    """
    if not Comment.is_valid_text(text):
        raise ValueError("Текст комментария не может быть пустым")
    comment_id = max((item.id for item in comments), default=0) + 1
    comment = Comment(
        comment_id,
        layout,
        author,
        text.strip(),
        comment_date,
        layout.version,
    )
    comments.append(comment)
    return comment


def get_layout_comments(
    comments: list[Comment],
    layout: Layout,
) -> list[Comment]:
    """Вернуть комментарии, относящиеся к указанному макету."""
    return [item for item in comments if item.layout.id == layout.id]


def has_comments(comments: list[Comment], layout: Layout) -> bool:
    """Проверить, есть ли у макета хотя бы один комментарий."""
    return len(get_layout_comments(comments, layout)) > 0


def count_comments_by_layout(comments: list[Comment]) -> dict[int, int]:
    """Посчитать количество комментариев для каждого макета."""
    statistics: dict[int, int] = {}
    for comment in comments:
        layout_id = comment.layout.id
        statistics[layout_id] = statistics.get(layout_id, 0) + 1
    return statistics
