"""Сервис согласования макетов.

Точка запуска приложения: меню и взаимодействие объектов
предметной области.
"""

from datetime import date

import storage
import utils
from models import Client, Comment, Designer, Layout
from models.comments import (add_comment, count_comments_by_layout,
                             get_layout_comments, has_comments)
from models.layouts import (add_layout, count_by_status, find_layout,
                            get_layout_by_id, sort_layouts)
from models.participants import find_participant_by_id

MENU = """
=== Сервис согласования макетов ===

1. Показать макеты
2. Найти макет по названию
3. Показать комментарии к макету
4. Добавить макет на согласование
5. Добавить комментарий клиента
6. Отправить макет на доработку
7. Утвердить макет
8. Показать статистику
9. Показать участников
0. Выход
"""


def show_layouts(layouts: list[Layout]) -> None:
    """Вывести список макетов, отсортированный по сроку."""
    if not layouts:
        print("Макетов пока нет")
        return
    for layout in sort_layouts(layouts):
        print(f"{layout.id}. {layout}")
        print(f"   {layout.designer.name} → {layout.client.name}")


def show_comments(comments: list[Comment], layout: Layout) -> None:
    """Вывести комментарии к выбранному макету."""
    selected = get_layout_comments(comments, layout)
    if not selected:
        print("Комментариев к этому макету нет")
        return
    for comment in selected:
        print(comment)


def show_participants(
    designers: list[Designer],
    clients: list[Client],
) -> None:
    """Вывести список дизайнеров и клиентов."""
    for participant in list(designers) + list(clients):
        print(f"{participant.id}. {participant}")


def ask_layout(layouts: list[Layout]) -> Layout | None:
    """Запросить идентификатор макета и вернуть найденный объект."""
    layout = get_layout_by_id(layouts, utils.input_int("Номер макета: "))
    if layout is None:
        print("Макет с таким номером не найден")
    return layout


def action_find_layout(layouts: list[Layout]) -> None:
    """Найти и вывести макеты по подстроке названия."""
    found = find_layout(layouts, utils.input_text("Часть названия: "))
    if found:
        show_layouts(found)
    else:
        print("Ничего не найдено")


def create_new_layout(
    layouts: list[Layout],
    designers: list[Designer],
    clients: list[Client],
) -> None:
    """Зарегистрировать новый макет на согласование."""
    designer = find_participant_by_id(
        designers, utils.input_int("Номер дизайнера: ")
    )
    if designer is None:
        print("Дизайнер не найден, макет не создан")
        return
    client = find_participant_by_id(
        clients, utils.input_int("Номер клиента: ")
    )
    if client is None:
        print("Клиент не найден, макет не создан")
        return
    title = utils.input_text("Название макета: ")
    sent_date = utils.input_date("Дата отправки (ДД.ММ.ГГГГ): ")
    approval_days = utils.input_int("Срок согласования, дней: ")
    layout = add_layout(
        layouts, title, designer, client, sent_date, approval_days
    )
    storage.save_layouts(layouts)
    print(f"Макет зарегистрирован: {layout}")
    print(f"Дней до окончания срока: {layout.days_left(date.today())}")


def create_new_comment(
    comments: list[Comment],
    layouts: list[Layout],
) -> None:
    """Добавить комментарий клиента к выбранному макету."""
    layout = ask_layout(layouts)
    if layout is None:
        return
    text = utils.input_text("Текст комментария: ")
    try:
        comment = add_comment(
            comments, layout, layout.client, text, date.today()
        )
    except ValueError as error:
        print(f"Ошибка: {error}")
        return
    storage.save_comments(comments)
    print(f"Добавлен комментарий: {comment}")


def change_layout_status(
    layouts: list[Layout],
    comments: list[Comment],
    approve: bool,
) -> None:
    """Утвердить макет или отправить его на доработку."""
    layout = ask_layout(layouts)
    if layout is None:
        return
    try:
        if approve:
            layout.approve()
        else:
            layout.send_to_revision()
    except ValueError as error:
        print(f"Ошибка: {error}")
        return
    storage.save_layouts(layouts)
    print(f"{layout}")
    if has_comments(comments, layout):
        print("У макета есть замечания клиента")


def show_statistics(
    layouts: list[Layout],
    comments: list[Comment],
) -> None:
    """Вывести статистику по статусам макетов и комментариям."""
    for status, amount in count_by_status(layouts).items():
        print(f"{status}: {amount}")
    for layout_id, amount in count_comments_by_layout(comments).items():
        layout = get_layout_by_id(layouts, layout_id)
        title = layout.title if layout else "макет удалён"
        print(f"Комментариев к «{title}»: {amount}")


def main() -> None:
    """Точка запуска приложения: загрузка данных и цикл меню."""
    designers = storage.load_designers()
    clients = storage.load_clients()
    layouts = storage.load_layouts(designers, clients)
    comments = storage.load_comments(layouts, clients)
    while True:
        print(MENU)
        choice = utils.input_int("Выберите действие: ")
        if choice == 0:
            storage.save_layouts(layouts)
            storage.save_comments(comments)
            print("Работа завершена")
            break
        elif choice == 1:
            show_layouts(layouts)
        elif choice == 2:
            action_find_layout(layouts)
        elif choice == 3:
            layout = ask_layout(layouts)
            if layout is not None:
                show_comments(comments, layout)
        elif choice == 4:
            create_new_layout(layouts, designers, clients)
        elif choice == 5:
            create_new_comment(comments, layouts)
        elif choice == 6:
            change_layout_status(layouts, comments, approve=False)
        elif choice == 7:
            change_layout_status(layouts, comments, approve=True)
        elif choice == 8:
            show_statistics(layouts, comments)
        elif choice == 9:
            show_participants(designers, clients)
        else:
            print("Такого пункта меню нет")


if __name__ == "__main__":
    main()
