"""Участники согласования макета: дизайнер и клиент.

Классы Designer и Client наследуются от общего класса Participant:
оба являются участниками согласования и хранят одинаковый набор
контактных данных, но по-разному представляются пользователю.
"""

from typing import Self, TypeVar


class Participant:
    """Участник согласования макета."""

    def __init__(
        self,
        participant_id: int,
        name: str,
        email: str,
    ) -> None:
        """Создать участника и сохранить его данные в атрибутах."""
        self.id = participant_id
        self.name = name
        self.email = email

    @property
    def role(self) -> str:
        """Название роли участника."""
        return "Участник"

    @classmethod
    def from_data(cls, data: dict) -> Self:
        """Создать участника из данных JSON."""
        return cls(data["id"], data["name"], data["email"])

    def to_data(self) -> dict:
        """Преобразовать участника в данные для сохранения в JSON."""
        return {"id": self.id, "name": self.name, "email": self.email}

    def __str__(self) -> str:
        """Строковое представление участника."""
        return f"{self.role} {self.name} ({self.email})"


class Designer(Participant):
    """Дизайнер — автор макета."""

    @property
    def role(self) -> str:
        """Название роли участника."""
        return "Дизайнер"


class Client(Participant):
    """Клиент — заказчик, согласующий макет."""

    def __init__(
        self,
        participant_id: int,
        name: str,
        email: str,
        company: str = "",
    ) -> None:
        """Создать клиента и дополнительно сохранить организацию."""
        super().__init__(participant_id, name, email)
        self.company = company

    @property
    def role(self) -> str:
        """Название роли участника."""
        return "Клиент"

    @classmethod
    def from_data(cls, data: dict) -> Self:
        """Создать клиента из данных JSON."""
        return cls(
            data["id"],
            data["name"],
            data["email"],
            data.get("company", ""),
        )

    def to_data(self) -> dict:
        """Преобразовать клиента в данные для сохранения в JSON."""
        data = super().to_data()
        data["company"] = self.company
        return data

    def __str__(self) -> str:
        """Строковое представление клиента с названием организации."""
        if self.company:
            return f"{self.role} {self.name}, {self.company}"
        return f"{self.role} {self.name} ({self.email})"


ParticipantT = TypeVar("ParticipantT", bound=Participant)


def add_designer(
    designers: list[Designer],
    name: str,
    email: str,
) -> Designer:
    """Добавить дизайнера в коллекцию и вернуть созданный объект."""
    designer_id = max((item.id for item in designers), default=0) + 1
    designer = Designer(designer_id, name, email)
    designers.append(designer)
    return designer


def add_client(
    clients: list[Client],
    name: str,
    email: str,
    company: str = "",
) -> Client:
    """Добавить клиента в коллекцию и вернуть созданный объект."""
    client_id = max((item.id for item in clients), default=0) + 1
    client = Client(client_id, name, email, company)
    clients.append(client)
    return client


def find_participant_by_id(
    participants: list[ParticipantT],
    participant_id: int,
) -> ParticipantT | None:
    """Найти участника по идентификатору или вернуть None.

    Тип результата совпадает с типом элементов коллекции: поиск
    в списке дизайнеров возвращает объект Designer, в списке
    клиентов — объект Client.
    """
    for participant in participants:
        if participant.id == participant_id:
            return participant
    return None


def find_participant(
    participants: list[ParticipantT],
    query: str,
) -> list[ParticipantT]:
    """Найти участников по подстроке имени без учёта регистра."""
    return [
        item for item in participants if query.lower() in item.name.lower()
    ]
