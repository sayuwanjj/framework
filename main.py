from datetime import date, timedelta


def register_layout(title, version, designer, client, sent_date, approval_days):
    """Регистрирует макет на согласование и возвращает срок ответа клиента."""
    deadline = sent_date + timedelta(days=int(approval_days))
    print("Макет зарегистрирован на согласование")
    print("Название: " + title + " (версия " + str(version) + ")")
    print("Дизайнер: " + designer)
    print("Клиент: " + client)
    print(f"Отправлен: {sent_date}, срок согласования до {deadline}")
    return deadline


def get_approval_status(is_approved, has_comments):
    """Определяет текущий статус согласования макета."""
    if is_approved:
        return "Утверждён"
    elif has_comments:
        return "На доработке"
    else:
        return "На согласовании"


def days_left(deadline, today):
    """Возвращает количество дней, оставшихся до окончания срока согласования."""
    return (deadline - today).days


def add_comment(author, text, comment_date, layout_version):
    """Добавляет комментарий клиента к макету и возвращает его текст."""
    if len(text) == 0:
        return "Комментарий не добавлен: текст пустой"
    comment = f"[{comment_date}] {author} (версия {layout_version}): {text}"
    print("Добавлен комментарий: " + comment)
    return comment


layout_title = "Главная страница интернет-магазина"
layout_version = 1
designer_name = "Грязнова Арина"
client_name = "ООО «Ромашка»"
sent_date = date(2026, 9, 10)
approval_days = "5"
today = date(2026, 9, 13)

deadline = register_layout(
    layout_title,
    layout_version,
    designer_name,
    client_name,
    sent_date,
    approval_days,
)

"""Добавление комментария клиента к макету."""
comment_text = "Увеличить логотип и заменить цвет кнопки на фирменный"
add_comment(client_name, comment_text, today, layout_version)

has_comments = len(comment_text) > 0
is_approved = False

print("Статус макета: " + get_approval_status(is_approved, has_comments))

"""Контроль срока согласования."""
remaining = days_left(deadline, today)
if remaining > 0:
    print(f"До окончания срока согласования осталось дней: {remaining}")
elif remaining == 0:
    print("Сегодня последний день согласования макета")
else:
    print(f"Срок согласования истёк {-remaining} дн. назад")