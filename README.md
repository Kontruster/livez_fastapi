# LiveZ — мини-соцсеть (FastAPI + React)

## Стек

- **Backend:** FastAPI, SQLAlchemy 2.0 (async), Alembic, PostgreSQL, fastapi-users
- **Frontend:** React 18 + Vite, React Router, чистый CSS
- **Инфраструктура:** Docker Compose

## Быстрый старт

### 1. Клонировать и подготовить env-файлы

```bash
git clone <repo-url>
cd livez_fastapi

cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
cp .env.example .env
```

Открой `backend/.env` и сгенерируй настоящий `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 2. Запустить

```bash
docker compose up --build
```

Дождись строк `Application startup complete.` в логах backend.

### 3. Применить миграции (один раз)

```bash
docker compose exec backend alembic upgrade head
```

### 4. Открыть

- Фронт: http://localhost:5173
- Swagger: http://localhost:8000/docs

## Разработка

### Локальный backend без Docker (для отладки в IDE)

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# убедиться, что БД поднята (docker compose up -d db)
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/livez

alembic upgrade head
uvicorn app.main:app --reload
```

### Локальный frontend

```bash
cd frontend
npm install
npm run dev
```

### Миграции

Создать новую миграцию после изменения моделей:

```bash
docker compose exec backend alembic revision --autogenerate -m "описание изменений"
docker compose exec backend alembic upgrade head
```

## Структура

```
livez_fastapi/
├── backend/          # FastAPI
│   ├── app/          # код приложения
│   ├── alembic/      # миграции
│   ├── uploads/      # загруженные картинки
│   └── .env.example
├── frontend/         # React + Vite
│   └── .env.example
├── docker-compose.yml
└── .env.example
```

## Переменные окружения

Все настройки описаны в `.env.example` в соответствующих папках.

**Ключевые:**

| Переменная | Где | Что |
|---|---|---|
| `SECRET_KEY` | backend/.env | секрет для JWT |
| `DATABASE_URL` | backend/.env | строка подключения к PostgreSQL |
| `CORS_ORIGINS` | backend/.env | список origin через запятую |
| `POSTGRES_*` | .env (корень) | креды БД для docker-compose |
| `VITE_BACKEND_URL` | frontend/.env.local | адрес бэкенда для прокси |

## Продакшн-заметки

- `DEBUG=false` в `backend/.env`
- `SECRET_KEY` — обязательно случайный, не из example
- `POSTGRES_PASSWORD` — сильный пароль
- `CORS_ORIGINS` — конкретный домен фронта, не `*`
- Аватарки и картинки постов — смонтированы в volume, переживут перезапуск контейнера
- Для HTTPS запускайте за nginx/Caddy — FastAPI сам TLS не терминирует