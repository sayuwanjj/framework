"""Сохранение и загрузка данных проекта в JSON-файлах.

Чтение и запись выполняются через контекстный менеджер with.
Отсутствие файла и некорректный JSON обрабатываются исключениями.
"""

import json
import os

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


def load_layouts(filename: str = LAYOUTS_FILE) -> list[dict]:
    """Загрузить макеты из JSON-файла."""
    return load_data(filename)


def save_layouts(layouts: list[dict], filename: str = LAYOUTS_FILE) -> None:
    """Сохранить макеты в JSON-файл."""
    save_data(filename, layouts)


def load_comments(filename: str = COMMENTS_FILE) -> list[dict]:
    """Загрузить комментарии из JSON-файла."""
    return load_data(filename)


def save_comments(
    comments: list[dict],
    filename: str = COMMENTS_FILE,
) -> None:
    """Сохранить комментарии в JSON-файл."""
    save_data(filename, comments)
