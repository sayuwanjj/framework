"""Макет, отправленный на согласование, и операции над коллекцией."""

from datetime import date, timedelta

from .participants import Client, Designer


class Layout:
    """Макет, отправленный дизайнером клиенту на согласование."""

    STATUS_REVIEW = "На согласовании"
    STATUS_REVISION = "На доработке"
    STATUS_APPROVED = "Утверждён"

    def __init__(
        self,
        layout_id: int,
        title: str,
        designer: Designer,
        client: Client,
        sent_date: date,
        approval_days: int,
        version: int = 1,
        status: str = STATUS_REVIEW,
    ) -> None:
        """Создать макет и сохранить переданные данные в атрибутах."""
        self.id = layout_id
        self.title = title
        self.designer = designer
        self.client = client
        self.sent_date = sent_date
        self.approval_days = int(approval_days)
        self.version = version
        self._status = status

    @property
    def status(self) -> str:
        """Текущий статус согласования макета."""
        return self._status

    @property
    def deadline(self) -> date:
        """Срок, до которого клиент должен ответить."""
        return self.sent_date + timedelta(days=self.approval_days)

    @property
    def is_approved(self) -> bool:
        """Признак того, что макет утверждён."""
        return self._status == Layout.STATUS_APPROVED

    def days_left(self, today: date) -> int:
        """Вернуть число дней, оставшихся до окончания срока."""
        return (self.deadline - today).days

    def approve(self) -> None:
        """Утвердить макет.

        Вызывает ValueError, если макет уже утверждён.
        """
        if self.is_approved:
            raise ValueError("Макет уже утверждён")
        self._status = Layout.STATUS_APPROVED

    def send_to_revision(self) -> None:
        """Отправить макет на доработку и создать следующую версию.

        Вызывает ValueError, если макет уже утверждён.
        """
        if self.is_approved:
            raise ValueError("Утверждённый макет не дорабатывается")
        self._status = Layout.STATUS_REVISION
        self.version += 1

    @classmethod
    def from_data(
        cls,
        data: dict,
        designer: Designer,
        client: Client,
    ) -> "Layout":
        """Создать макет из данных JSON и найденных участников."""
        return cls(
            layout_id=data["id"],
            title=data["title"],
            designer=designer,
            client=client,
            sent_date=date.fromisoformat(data["sent_date"]),
            approval_days=data["approval_days"],
            version=data["version"],
            status=data["status"],
        )

    def to_data(self) -> dict:
        """Преобразовать макет в данные для сохранения в JSON."""
        return {
            "id": self.id,
            "title": self.title,
            "version": self.version,
            "designer_id": self.designer.id,
            "client_id": self.client.id,
            "sent_date": self.sent_date.isoformat(),
            "approval_days": self.approval_days,
            "status": self._status,
        }

    def __str__(self) -> str:
        """Строковое представление макета."""
        return (
            f"{self.title} (версия {self.version}) — {self._status}, "
            f"срок до {self.deadline}"
        )


def add_layout(
    layouts: list[Layout],
    title: str,
    designer: Designer,
    client: Client,
    sent_date: date,
    approval_days: int,
) -> Layout:
    """Создать макет, добавить его в коллекцию и вернуть объект."""
    layout_id = max((item.id for item in layouts), default=0) + 1
    layout = Layout(
        layout_id,
        title,
        designer,
        client,
        sent_date,
        approval_days,
    )
    layouts.append(layout)
    return layout


def get_layout_by_id(layouts: list[Layout], layout_id: int) -> Layout | None:
    """Найти макет по идентификатору или вернуть None."""
    for layout in layouts:
        if layout.id == layout_id:
            return layout
    return None


def find_layout(layouts: list[Layout], query: str) -> list[Layout]:
    """Найти макеты по подстроке названия без учёта регистра."""
    return [item for item in layouts if query.lower() in item.title.lower()]


def filter_layouts_by_status(
    layouts: list[Layout],
    status: str,
) -> list[Layout]:
    """Отобрать макеты с указанным статусом с помощью генератора."""
    selected = (item for item in layouts if item.status == status)
    return list(selected)


def sort_layouts(layouts: list[Layout]) -> list[Layout]:
    """Отсортировать макеты по сроку согласования (lambda-функция)."""
    return sorted(layouts, key=lambda layout: layout.deadline)


def count_by_status(layouts: list[Layout]) -> dict[str, int]:
    """Посчитать количество макетов по каждому статусу."""
    statistics = {
        Layout.STATUS_REVIEW: 0,
        Layout.STATUS_REVISION: 0,
        Layout.STATUS_APPROVED: 0,
    }
    for layout in layouts:
        statistics[layout.status] = statistics.get(layout.status, 0) + 1
    return statistics
