# Сервис links

Владеет созданием коротких ссылок, пользовательскими slug и перенаправлениями.

## Версии

Python 3.14.8 закреплён в `.python-version` и Dockerfile. Минимальные версии прямых зависимостей указаны в `pyproject.toml`, точные версии всех библиотек — в `uv.lock`. Для установки используйте актуальный uv с поддержкой скачивания Python 3.14.8.

## Короткие команды

Частые команды собраны в `justfile` (нужен [just](https://github.com/casey/just): `brew install just`):

```bash
just             # список команд
just lint        # isort + ruff check + ruff format --check
just fmt         # исправить и отформатировать
just test        # все тесты; аргументы уходят в pytest: just test tests/unit -x
just test-fast   # без тестов на Docker
just test-docker # тесты только с Docker
just check       # lint + test, перед коммитом
```

Ниже — те же команды без `just`.

## Запуск

Команды выполняются из `services/links` при доступном PostgreSQL:

```bash
uv sync --frozen
uv run uvicorn links.main:app --app-dir src --reload
```

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

```bash
uv run pytest
uv run pytest --cov=links
```

Исходники находятся в `src/links`. Проект использует существующий режим uv без установки собственного пакета: при запуске Uvicorn передаётся `--app-dir src`, а pytest добавляет `src` через конфигурацию в `pyproject.toml`.

Dockerfile собирается с контекстом этого каталога. Настройки подключения к PostgreSQL перечислены в `.env.example`; значения читаются из окружения. Миграции пока не подключены.
