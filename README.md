# Link Shortener

Сервис сокращения ссылок на Python 3.14.8, FastAPI и SQLAlchemy с PostgreSQL.

## Структура

```text
services/
  links/                  # Самостоятельное приложение сокращения ссылок
    src/links/
      main.py             # Сборка FastAPI-приложения
      settings.py         # Настройки БД и CORS
      api/                # Маршруты, HTTP-схемы и зависимости
      application/        # Бизнес-сценарии и интерфейс репозитория
      domain/             # Генерация slug, валидация и исключения
      infrastructure/     # SQLAlchemy, модели и реализация репозитория
    tests/                # Unit- и интеграционные тесты
    migrations/           # Место для будущих миграций
    pyproject.toml
    uv.lock
    Dockerfile
  analytics/              # Место для будущего сервиса аналитики
contracts/                # HTTP-контракты и схемы событий
infra/compose.yaml        # Локальный запуск сервисов
tests/e2e/               # Место для будущих сквозных тестов
docs/architecture.md     # Границы компонентов и сервисов
```

## Запуск через Docker

Из корня репозитория:

```bash
docker compose -f infra/compose.yaml up --build
```

API: http://localhost:8000. Swagger UI: http://localhost:8000/docs.
Образ собирается из `services/links`; PostgreSQL хранит данные в томе `postgres_data`.
При переходе с прежнего Compose сохраняйте прежнее имя Compose-проекта через `-p`, чтобы использовать существующий том.

## Локальная разработка

Из корня запустите PostgreSQL:

```bash
docker compose -f infra/compose.yaml up -d db
```

Затем перейдите в каталог сервиса:

```bash
cd services/links
uv sync --frozen
uv run uvicorn links.main:app --app-dir src --reload
```

Настройки подключения читаются из переменных окружения `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`. Пример значений — `services/links/.env.example`. Файл `.env` автоматически не загружается: передавайте переменные через окружение или настройки запуска.

## API

- `GET /` — `{"status": "ok"}`.
- `POST /shorten_url` — тело `{"long_url": "https://example.com"}`.
- `POST /custom_url` — тело `{"origin_url": "https://example.com", "custom_url": "my-link"}`.
- `GET /{slug}` — перенаправление на исходный URL с кодом 302.

Оба метода создания возвращают `{"data": "slug"}`. Маршруты, коды ответа, валидация и настройки CORS сохранены.

## Линтер и форматирование

Команды выполняются из `services/links`:

```bash
uv run isort . --check-only
uv run ruff check .
uv run ruff format --check .
```

Для автоматического исправления и форматирования:

```bash
uv run ruff check . --fix
uv run isort .
uv run ruff format .
```

Ruff настроен в `pyproject.toml`: Python 3.14, длина строки 100 символов, правила `E4`, `E7`, `E9` и `F` для базовых ошибок и неиспользуемых импортов. Сортировкой импортов занимается isort: при двух и более именах из одного модуля используются скобки, отдельные строки и завершающая запятая (`force_grid_wrap = 2`). Ruff сохраняет это оформление благодаря `skip-magic-trailing-comma = false`. Проверяется исходный код и тесты. Подробнее: [документация Ruff](https://docs.astral.sh/ruff/configuration/).

## Тесты

Из каталога `services/links`:

```bash
uv run pytest
uv run pytest --cov=links
```

Из корня с уже подготовленным окружением сервиса:

```bash
services/links/.venv/bin/python -m pytest
```

Интеграционные тесты используют отдельную SQLite в памяти и не изменяют PostgreSQL или файл `test.db`.

Миграции Alembic и сервис аналитики пока не подключены. Приложение по-прежнему создаёт отсутствующие таблицы через `create_all` при запуске.
