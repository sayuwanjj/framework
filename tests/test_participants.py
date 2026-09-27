"""Тесты классов участников согласования."""

from models import Client, Designer
from models.participants import (
    add_client,
    add_designer,
    find_participant,
    find_participant_by_id,
)


def test_designer_creation():
    designer = Designer(1, "Грязнова Арина", "arina@example.com")
    assert designer.id == 1
    assert designer.name == "Грязнова Арина"
    assert designer.email == "arina@example.com"


def test_client_has_company():
    client = Client(1, "Иванов Пётр", "p@example.com", "ООО «Ромашка»")
    assert client.company == "ООО «Ромашка»"
    assert "ООО «Ромашка»" in str(client)


def test_role_is_polymorphic():
    designer = Designer(1, "Арина", "a@example.com")
    client = Client(2, "Пётр", "p@example.com")
    assert designer.role == "Дизайнер"
    assert client.role == "Клиент"
    assert str(designer) != str(client)


def test_client_from_data_and_to_data():
    data = {
        "id": 3,
        "name": "Кузнецов Олег",
        "email": "oleg@example.com",
        "company": "ИП Кузнецов",
    }
    client = Client.from_data(data)
    assert client.id == 3
    assert client.to_data() == data


def test_add_and_find_participants():
    designers = []
    add_designer(designers, "Арина", "a@example.com")
    add_designer(designers, "Илья", "i@example.com")
    clients = []
    add_client(clients, "Пётр", "p@example.com", "ООО «Ромашка»")
    assert len(designers) == 2
    assert find_participant_by_id(designers, 2).name == "Илья"
    assert find_participant_by_id(designers, 99) is None
    assert find_participant(clients, "пётр")
