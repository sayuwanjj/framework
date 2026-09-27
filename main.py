"""Сервис согласования макетов.

Точка запуска приложения: меню и вызов функций проекта.
"""

from datetime import date

import comments as comments_module
import layouts as layouts_module
import storage
import utils

MENU = """
=== Сервис согласования макетов ===

1. Показать макеты
2. Найти макет по названию
3. Показать комментарии к макету
4. Добавить макет на согласование
5. Добавить комментарий клиента
6. Отправить макет на доработку
7. Утвердить макет
8. Показать статистику по статусам
0. Выход
"""


def show_layouts(layouts: list[dict]) -> None:
    """Вывести список макетов в виде таблицы."""
    if not layouts:
        print("Макетов пока нет")
        return
    print(f"{'id':>3} {'Макет':<36} {'Вер.':>4} "
          f"{'Срок':<12} {'Статус':<16}")
    for layout in layouts_module.sort_layouts(layouts):
        print(f"{layout['id']:>3} {layout['title'][:36]:<36} "
              f"{layout['version']:>4} {layout['deadline']:<12} "
              f"{layout['status']:<16}")


def show_comments(comments: list[dict], layout_id: int) -> None:
    """Вывести комментарии к выбранному макету."""
    selected = comments_module.get_layout_comments(comments, layout_id)
    if not selected:
        print("Комментариев к этому макету нет")
        return
    for comment in selected:
        print(comments_module.format_comment(comment))


def action_find_layout(layouts: list[dict]) -> None:
    """Найти и вывести макеты по подстроке названия."""
    query = utils.input_text("Часть названия макета: ")
    found = layouts_module.find_layout(layouts, query)
    if found:
        show_layouts(found)
    else:
        print("Ничего не найдено")


def action_add_layout(layouts: list[dict]) -> None:
    """Зарегистрировать новый макет на согласование."""
    title = utils.input_text("Название макета: ")
    designer = utils.input_text("Дизайнер: ")
    client = utils.input_text("Клиент: ")
    sent_date = utils.input_date("Дата отправки (ДД.ММ.ГГГГ): ")
    approval_days = utils.input_int("Срок согласования, дней: ")
    layout = layouts_module.add_layout(
        layouts, title, designer, client, sent_date, approval_days
    )
    storage.save_layouts(layouts)
    layouts_module.register_layout(
        layout["title"],
        layout["version"],
        layout["designer"],
        layout["client"],
        sent_date,
        approval_days,
    )
    remaining = layouts_module.days_left(
        date.fromisoformat(layout["deadline"]), date.today()
    )
    print(f"Дней до окончания срока согласования: {remaining}")


def action_add_comment(layouts: list[dict], comments: list[dict]) -> None:
    """Добавить комментарий клиента к макету."""
    layout_id = utils.input_int("Идентификатор макета: ")
    layout = layouts_module.get_layout_by_id(layouts, layout_id)
    if layout is None:
        print("Макет с таким идентификатором не найден")
        return
    author = utils.input_text("Автор комментария: ")
    text = utils.input_text("Текст комментария: ")
    try:
        comment = comments_module.add_comment(
            comments,
            layout_id,
            author,
            text,
            date.today(),
            layout["version"],
        )
    except ValueError as error:
        print(f"Ошибка: {error}")
        return
    storage.save_comments(comments)
    print("Добавлен комментарий: "
          + comments_module.format_comment(comment))


def action_change_status(
    layouts: list[dict],
    comments: list[dict],
    approve: bool,
) -> None:
    """Утвердить макет или отправить его на доработку."""
    layout_id = utils.input_int("Идентификатор макета: ")
    try:
        if approve:
            layout = layouts_module.approve_layout(layouts, layout_id)
        else:
            layout = layouts_module.send_to_revision(layouts, layout_id)
    except ValueError as error:
        print(f"Ошибка: {error}")
        return
    storage.save_layouts(layouts)
    status = layouts_module.get_approval_status(
        approve,
        comments_module.has_comments(comments, layout_id),
    )
    print(f"Макет «{layout['title']}» — {status}, "
          f"версия {layout['version']}")


def action_statistics(layouts: list[dict], comments: list[dict]) -> None:
    """Вывести статистику по статусам макетов и комментариям."""
    statistics = layouts_module.count_by_status(layouts)
    for status, amount in statistics.items():
        print(f"{status}: {amount}")
    print(f"Всего комментариев: {len(comments)}")


def main() -> None:
    """Точка запуска приложения: цикл меню и вызов функций."""
    layouts = storage.load_layouts()
    comments = storage.load_comments()
    while True:
        print(MENU)
        choice = utils.input_int("Выберите действие: ")
        if choice == 0:
            print("Работа завершена")
            break
        elif choice == 1:
            show_layouts(layouts)
        elif choice == 2:
            action_find_layout(layouts)
        elif choice == 3:
            show_comments(comments, utils.input_int("Идентификатор: "))
        elif choice == 4:
            action_add_layout(layouts)
        elif choice == 5:
            action_add_comment(layouts, comments)
        elif choice == 6:
            action_change_status(layouts, comments, approve=False)
        elif choice == 7:
            action_change_status(layouts, comments, approve=True)
        elif choice == 8:
            action_statistics(layouts, comments)
        else:
            print("Такого пункта меню нет")


if __name__ == "__main__":
    main()
