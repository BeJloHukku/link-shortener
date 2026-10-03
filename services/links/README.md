# Сервис links

Владеет созданием коротких ссылок, пользовательскими slug и перенаправлениями.

## Версии

Python 3.14.8 закреплён в `.python-version` и Dockerfile. Минимальные версии прямых зависимостей указаны в `pyproject.toml`, точные версии всех библиотек — в `uv.lock`. Для установки используйте актуальный uv с поддержкой скачивания Python 3.14.8.

## Запуск

Команды выполняются из `services/links` при доступном PostgreSQL:

```bash
uv sync --frozen
uv run uvicorn links.main:app --app-dir src --reload
```

## Тесты

```bash
uv run pytest
uv run pytest --cov=links
```

Исходники находятся в `src/links`. Проект использует существующий режим uv без установки собственного пакета: при запуске Uvicorn передаётся `--app-dir src`, а pytest добавляет `src` через конфигурацию в `pyproject.toml`.

Dockerfile собирается с контекстом этого каталога. Настройки подключения к PostgreSQL перечислены в `.env.example`; значения читаются из окружения. Миграции пока не подключены.
