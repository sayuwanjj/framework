"""Сохранение и загрузка данных проекта в JSON-файлах.

JSON остаётся форматом хранения: при загрузке данные преобразуются
в объекты классов предметной области, при сохранении объекты
преобразуются обратно в данные. Связанные объекты хранятся в файлах
по их идентификаторам.
"""

import json
import os

from models import Client, Comment, Designer, Layout
from models.layouts import get_layout_by_id
from models.participants import find_participant_by_id

DESIGNERS_FILE = os.path.join("data", "designers.json")
CLIENTS_FILE = os.path.join("data", "clients.json")
LAYOUTS_FILE = os.path.join("data", "layouts.json")
COMMENTS_FILE = os.path.join("data", "comments.json")


def load_data(filename: str) -> list[dict]:
    """Загрузить список записей из JSON-файла.

    Если файл отсутствует или содержит некорректный JSON,
    возвращается пустой список, а программа продолжает работу.
    """
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Файл {filename} не найден, используется пустой список")
        return []
    except json.JSONDecodeError:
        print(f"Файл {filename} повреждён, используется пустой список")
        return []


def save_data(filename: str, items: list[dict]) -> None:
    """Сохранить список записей в JSON-файл."""
    directory = os.path.dirname(filename)
    if directory:
        os.makedirs(directory, exist_ok=True)
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(items, file, ensure_ascii=False, indent=4)
    except OSError as error:
        print(f"Не удалось сохранить файл {filename}: {error}")


def load_designers(filename: str = DESIGNERS_FILE) -> list[Designer]:
    """Загрузить дизайнеров и создать объекты Designer."""
    return [Designer.from_data(item) for item in load_data(filename)]


def save_designers(
    designers: list[Designer],
    filename: str = DESIGNERS_FILE,
) -> None:
    """Сохранить объекты Designer в JSON-файл."""
    save_data(filename, [item.to_data() for item in designers])


def load_clients(filename: str = CLIENTS_FILE) -> list[Client]:
    """Загрузить клиентов и создать объекты Client."""
    return [Client.from_data(item) for item in load_data(filename)]


def save_clients(
    clients: list[Client],
    filename: str = CLIENTS_FILE,
) -> None:
    """Сохранить объекты Client в JSON-файл."""
    save_data(filename, [item.to_data() for item in clients])


def load_layouts(
    designers: list[Designer],
    clients: list[Client],
    filename: str = LAYOUTS_FILE,
) -> list[Layout]:
    """Загрузить макеты и связать их с дизайнерами и клиентами.

    Запись пропускается, если указанный дизайнер или клиент
    отсутствует в загруженных коллекциях.
    """
    layouts = []
    for item in load_data(filename):
        designer = find_participant_by_id(designers, item["designer_id"])
        client = find_participant_by_id(clients, item["client_id"])
        if designer is None or client is None:
            print(f"Макет {item['id']} пропущен: участник не найден")
            continue
        layouts.append(Layout.from_data(item, designer, client))
    return layouts


def save_layouts(
    layouts: list[Layout],
    filename: str = LAYOUTS_FILE,
) -> None:
    """Сохранить объекты Layout в JSON-файл."""
    save_data(filename, [item.to_data() for item in layouts])


def load_comments(
    layouts: list[Layout],
    clients: list[Client],
    filename: str = COMMENTS_FILE,
) -> list[Comment]:
    """Загрузить комментарии и связать их с макетами и клиентами.

    Запись пропускается, если макет или автор не найдены.
    """
    comments = []
    for item in load_data(filename):
        layout = get_layout_by_id(layouts, item["layout_id"])
        author = find_participant_by_id(clients, item["author_id"])
        if layout is None or author is None:
            print(f"Комментарий {item['id']} пропущен: объект не найден")
            continue
        comments.append(Comment.from_data(item, layout, author))
    return comments


def save_comments(
    comments: list[Comment],
    filename: str = COMMENTS_FILE,
) -> None:
    """Сохранить объекты Comment в JSON-файл."""
    save_data(filename, [item.to_data() for item in comments])
