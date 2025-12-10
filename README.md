# Link Shortener

Современный сервис для сокращения URL-адресов с веб-интерфейсом и REST API.

## Возможности

- Автоматическая генерация коротких ссылок
- Создание пользовательских URL (custom slugs)
- Быстрое перенаправление с кешированием
- PostgreSQL для надежного хранения данных
- Полная контейнеризация с Docker
- Современный веб-интерфейс
- REST API с документацией

## Технологии

- **Backend**: Python 3.13, FastAPI, SQLAlchemy (async)
- **Database**: PostgreSQL 17
- **Frontend**: HTML5, CSS3, JavaScript
- **Containerization**: Docker, Docker Compose
- **Package Manager**: uv

## Установка и запуск

### С Docker (рекомендуется)

```bash
# Клонировать репозиторий
git clone https://github.com/BeJloHukku/link-shortener.git
cd link-shortener

# Запустить с Docker Compose
docker-compose up
```

Сервис будет доступен по адресу: **http://localhost:8000**

### Локальная разработка

```bash
# Установить зависимости
pip install uv
uv sync

# Запустить PostgreSQL в Docker
docker-compose up db

# Активировать виртуальное окружение
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Запустить сервер
uvicorn src.main:app --reload
```

## API Documentation

После запуска документация доступна по адресу:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Основные эндпоинты

#### POST `/shorten_url` - Создать короткую ссылку
```json
{
  "long_url": "https://example.com"
}
```

**Ответ:**
```json
{
  "data": "/abc123"
}
```

#### POST `/custom_url` - Создать пользовательскую ссылку
```json
{
  "origin_url": "https://example.com",
  "custom_url": "my-link"
}
```

**Ответ:**
```json
{
  "data": "/my-link"
}
```

#### GET `/{slug}` - Перенаправление
Перенаправляет на оригинальный URL.

## Веб-интерфейс

Интерфейс доступен на главной странице и предоставляет:
- Форму для создания автоматических коротких ссылок
- Форму для создания пользовательских URL
- Копирование ссылок в буфер обмена
- Адаптивный дизайн для мобильных устройств

## Тестирование

```bash
# Запустить тесты
pytest

# С покрытием
pytest --cov=src
```

## Структура проекта

```
link-shortener/
├── src/
│   ├── datebase/
│   │   ├── crud.py          # CRUD операции
│   │   ├── db.py            # Подключение к БД
│   │   └── models.py        # SQLAlchemy модели
│   ├── exeptions.py         # Кастомные исключения
│   ├── main.py              # FastAPI приложение
│   ├── retry_decorator.py   # Декоратор для retry логики
│   ├── service.py           # Бизнес-логика
│   ├── shortener.py         # Генерация slug
│   └── url_validator.py     # Валидация URL
├── static/
│   ├── index.html           # Веб-интерфейс
│   ├── script.js            # Клиентская логика
│   └── style.css            # Стили
├── tests/                   # Тесты
├── Dockerfile               # Docker образ
├── docker-compose.yml       # Docker Compose конфигурация
├── pyproject.toml           # Зависимости проекта
└── pytest.ini               # Конфигурация pytest
```

## Docker Hub

Образ доступен на Docker Hub:
```bash
docker pull bejlohukku/link-shortener:latest
```

## Автор

**BeJloHukku**

- GitHub: [@BeJloHukku](https://github.com/BeJloHukku)
- Docker Hub: [bejlohukku](https://hub.docker.com/u/bejlohukku)

## Вклад

Pull requests приветствуются! Для крупных изменений сначала откройте issue для обсуждения.

---

⭐️ Если проект понравился, поставьте звезду на GitHub!
