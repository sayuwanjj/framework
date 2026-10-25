-- Схема базы данных сервиса согласования макетов (ПР7).
-- IF NOT EXISTS позволяет запускать скрипт повторно:
-- существующие таблицы не пересоздаются и ошибки не возникает.

-- Дизайнеры, которые отправляют макеты на согласование.
CREATE TABLE IF NOT EXISTS designers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE
);

-- Клиенты, которые согласуют макеты и оставляют комментарии.
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    company TEXT
);

-- Макеты: каждый связан с одним дизайнером и одним клиентом.
CREATE TABLE IF NOT EXISTS layouts (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    designer_id INTEGER NOT NULL,
    client_id INTEGER NOT NULL,
    sent_date TEXT NOT NULL,
    approval_days INTEGER NOT NULL CHECK (approval_days > 0),
    status TEXT NOT NULL DEFAULT 'На согласовании',
    FOREIGN KEY (designer_id) REFERENCES designers(id),
    FOREIGN KEY (client_id) REFERENCES clients(id)
);

-- Комментарии клиентов к макетам.
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY,
    layout_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    comment_date TEXT NOT NULL,
    layout_version INTEGER NOT NULL,
    FOREIGN KEY (layout_id) REFERENCES layouts(id),
    FOREIGN KEY (author_id) REFERENCES clients(id)
);
