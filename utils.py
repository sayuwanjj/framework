"""Вспомогательные функции ввода данных с обработкой ошибок."""

from datetime import date, datetime

DATE_FORMAT = "%d.%m.%Y"


def input_text(prompt: str) -> str:
    """Запросить непустую строку. Запрос повторяется при ошибке."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Значение не может быть пустым, повторите ввод")


def input_int(prompt: str) -> int:
    """Запросить целое число. Запрос повторяется при ошибке ввода."""
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Нужно ввести целое число, повторите ввод")


def input_date(prompt: str) -> date:
    """Запросить дату в формате ДД.ММ.ГГГГ с повтором при ошибке."""
    while True:
        value = input(prompt).strip()
        try:
            return datetime.strptime(value, DATE_FORMAT).date()
        except ValueError:
            print("Неверный формат даты, введите её как 15.09.2026")
