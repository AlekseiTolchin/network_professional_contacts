# Социальная сеть профессиональных контактов

Учебный проект — клиент-серверное веб-приложение на Python (FastAPI) с PostgreSQL.

**Вариант 10** — «Социальная сеть профессиональных контактов».

## Стек технологий

- **Backend:** Python 3.12, FastAPI, SQLAlchemy ORM
- **Frontend:** Jinja2-шаблоны, Bootstrap 5 (CDN)
- **БД:** PostgreSQL 16
- **Аутентификация:** passlib + bcrypt, cookie-сессии
- **Инфраструктура:** Docker, docker-compose, python-dotenv

## Структура БД

| Таблица        | Описание                          |
|----------------|-----------------------------------|
| profiles       | Профили пользователей             |
| connections    | Профессиональные контакты         |
| posts          | Публикации                        |
| skills         | Навыки                            |
| profile_skills | Связь профилей и навыков (M2M)    |
| messages       | Личные сообщения                  |
| users          | Учётные записи для авторизации    |

### Ограничения

- `username` — уникальный
- `skill_name` — уникальный
- Нельзя создать connection, где `from_profile_id = to_profile_id`
- Уникальность пары `(profile_id, skill_id)` в `profile_skills`
- Каскадное удаление: удаление профиля удаляет его посты, сообщения, контакты, навыки профиля

## Настройка окружения

Перед запуском создайте файл `.env` в корне проекта на основе `.env.example`:

```bash
cp .env.example .env
```

Содержимое `.env`:

```
# Подключение к БД (для приложения)
DATABASE_URL=postgresql://practice_user:practice_password@db:5432/practice_db

# Учётные данные PostgreSQL (для контейнера db)
POSTGRES_DB=practice_db
POSTGRES_USER=practice_user
POSTGRES_PASSWORD=practice_password

# Секретный ключ для подписания cookie-сессий
SECRET_KEY=замените-на-случайную-строку
```

> **Важно:** `.env` содержит секреты и не должен попадать в Git (уже добавлен в `.gitignore`).  
> Для генерации `SECRET_KEY` можно использовать: `python -c "import secrets; print(secrets.token_hex(32))"`

## Запуск

```bash
docker compose up --build
```

Приложение доступно по адресу: **http://localhost:8000**

## Тестовые учётные записи

| Логин  | Пароль    | Роль  |
|--------|-----------|-------|
| admin  | admin123  | admin |
| user   | user123   | user  |

## Роли

- **admin** — полный CRUD по всем разделам, управление пользователями
- **user** — просмотр всех разделов (только чтение)

## Структура проекта

```
project/
├── app/
│   ├── __init__.py
│   ├── main.py          # Маршруты FastAPI
│   ├── database.py      # Подключение к БД
│   ├── models.py        # SQLAlchemy-модели
│   ├── auth.py          # Авторизация, хеширование
│   ├── crud.py          # CRUD-операции
│   ├── seed.py          # Начальные данные
│   ├── templates/       # Jinja2-шаблоны
│   └── static/          # CSS
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env              # секреты (не в Git)
├── .env.example      # шаблон для .env
├── .dockerignore
├── .gitignore
└── README.md
```

## PostgreSQL

- **database:** practice_db
- **user:** practice_user
- **password:** practice_password
- **port:** 5432
