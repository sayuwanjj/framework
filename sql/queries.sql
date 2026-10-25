-- SQL-запросы сервиса согласования макетов (ПР7).
-- Каждый запрос проверен в SQLite на базе data/layout_service.sqlite.
-- Значения в кавычках ('2026-09-20', 'Утверждён' и т. п.) указаны
-- для проверки: в Django-представлениях они передаются параметрами ?.


-- ===== 1. Выборка списков (SELECT ... FROM ... ORDER BY) =====

-- Запрос 1. Список всех макетов, отсортированный по дате отправки.
SELECT
    id,
    title,
    version,
    status,
    sent_date
FROM layouts
ORDER BY sent_date;

-- Запрос 2. Список дизайнеров в алфавитном порядке.
SELECT
    id,
    name,
    email
FROM designers
ORDER BY name;


-- ===== 2. Фильтрация (WHERE) =====

-- Запрос 3. Макеты с заданным статусом
-- (в Django: страница «Поиск макетов», параметр status).
SELECT
    id,
    title,
    status
FROM layouts
WHERE status = 'На согласовании'
ORDER BY title;

-- Запрос 4. Поиск макетов по части названия
-- (в Django: страница «Поиск макетов», параметр q).
SELECT
    id,
    title,
    status
FROM layouts
WHERE title LIKE '%товар%'
ORDER BY title;

-- Запрос 5. Неутверждённые макеты, срок согласования которых истёк
-- к выбранной дате (несколько условий: статус и дата).
-- Срок = дата отправки + approval_days дней.
SELECT
    id,
    title,
    status,
    date(sent_date, '+' || approval_days || ' days') AS deadline
FROM layouts
WHERE status != 'Утверждён'
    AND date(sent_date, '+' || approval_days || ' days') < '2026-09-20'
ORDER BY deadline;


-- ===== 3. Соединение таблиц (JOIN) =====

-- Запрос 6. Макеты с именами дизайнера и клиента (три таблицы).
SELECT
    layouts.id,
    layouts.title,
    layouts.version,
    layouts.status,
    date(
        layouts.sent_date, '+' || layouts.approval_days || ' days'
    ) AS deadline,
    designers.name AS designer_name,
    clients.name AS client_name
FROM layouts
JOIN designers ON layouts.designer_id = designers.id
JOIN clients ON layouts.client_id = clients.id
ORDER BY deadline;

-- Запрос 7. Комментарии с названием макета и именем автора.
SELECT
    comments.id,
    comments.text,
    comments.comment_date,
    comments.layout_version,
    layouts.title AS layout_title,
    clients.name AS author_name
FROM comments
JOIN layouts ON comments.layout_id = layouts.id
JOIN clients ON comments.author_id = clients.id
ORDER BY comments.comment_date DESC, comments.id;


-- ===== 4. Агрегатные функции (COUNT) =====

-- Запрос 8. Общее количество макетов.
SELECT COUNT(*) AS layouts_count
FROM layouts;

-- Запрос 9. Количество макетов, ожидающих ответа клиента
-- (все, кроме утверждённых).
SELECT COUNT(*) AS waiting_count
FROM layouts
WHERE status != 'Утверждён';

-- Запрос 10. Количество комментариев к выбранному макету.
SELECT COUNT(*) AS comments_count
FROM comments
WHERE layout_id = 1;


-- ===== 5. Группировка (GROUP BY) =====

-- Запрос 11. Количество макетов по статусам.
SELECT
    status,
    COUNT(*) AS layouts_count
FROM layouts
GROUP BY status
ORDER BY layouts_count DESC, status;

-- Запрос 12. Количество макетов у каждого дизайнера
-- (LEFT JOIN оставляет дизайнеров без макетов со значением 0).
SELECT
    designers.name AS designer_name,
    COUNT(layouts.id) AS layouts_count
FROM designers
LEFT JOIN layouts ON designers.id = layouts.designer_id
GROUP BY designers.id, designers.name
ORDER BY layouts_count DESC, designer_name;

-- Запрос 13. Количество комментариев к каждому макету.
SELECT
    layouts.id,
    layouts.title,
    COUNT(comments.id) AS comments_count
FROM layouts
LEFT JOIN comments ON layouts.id = comments.layout_id
GROUP BY layouts.id, layouts.title
ORDER BY comments_count DESC, layouts.title;


-- ===== 6. Фильтрация групп (HAVING) =====

-- Запрос 14. Макеты, к которым оставлено не меньше 2 комментариев.
SELECT
    layouts.id,
    layouts.title,
    COUNT(comments.id) AS comments_count
FROM layouts
JOIN comments ON layouts.id = comments.layout_id
GROUP BY layouts.id, layouts.title
HAVING COUNT(comments.id) >= 2
ORDER BY comments_count DESC;


-- ===== 7. Подзапрос (NOT IN) =====

-- Запрос 15. Макеты, к которым ещё нет ни одного комментария.
SELECT
    id,
    title,
    status
FROM layouts
WHERE id NOT IN (
    SELECT layout_id
    FROM comments
)
ORDER BY title;
