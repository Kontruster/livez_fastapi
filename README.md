# LiveZ — мини-соцсеть (FastAPI + React)

Лента постов с картинками, группы, комментарии, лайки, подписки, профили и настройки аккаунта.

## Стек

- **Backend:** FastAPI, SQLAlchemy 2.0 (async), Alembic, PostgreSQL, fastapi-users
- **Frontend:** React 19 + Vite, React Router, чистый CSS
- **Инфраструктура:** Docker Compose (dev и prod), nginx для прода
- **Качество:** pytest (54 теста), ruff, mypy, oxlint, prettier, GitHub Actions

## Структура

```
livez_fastapi/
├── backend/
│   ├── app/
│   │   ├── routers/        # HTTP-слой
│   │   ├── services/       # бизнес-логика
│   │   ├── repositories/   # доступ к данным
│   │   ├── core/auth.py    # fastapi-users: JWT + cookie
│   │   ├── config.py       # настройки из .env
│   │   ├── handlers.py     # централизованные обработчики ошибок
│   │   └── models.py       # таблицы
│   ├── alembic/            # миграции
│   ├── tests/              # pytest
│   └── uploads/            # аватарки и картинки постов
├── frontend/               # React + Vite
├── scripts/                # скрипты локального запуска
├── docker-compose.yml      # dev
├── docker-compose.prod.yml # prod
└── Makefile                # типовые команды
```

---

## Быстрый старт: Docker (рекомендуется)

Нужен только установленный Docker.

### 1. Подготовить env-файлы

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Откройте `backend/.env` и сгенерируйте настоящий `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 2. Запустить

```bash
docker compose up --build
```

Миграции применяются автоматически при старте backend — ждать и запускать
что-то вручную не нужно. Дождитесь строки `Application startup complete.`

### 3. Открыть

| Что | Адрес |
|---|---|
| Фронт | http://localhost:5173 |
| Swagger | http://localhost:8000/docs |
| Healthcheck | http://localhost:8000/health |

---

## Быстрый старт: локально через терминал

Без Docker: нужен Python 3.11+ и Node.js 20+. **PostgreSQL не обязателен** —
скрипты по умолчанию используют SQLite.

### Windows (PowerShell)

Два окна терминала:

```powershell
# окно 1 — backend
.\scripts\dev-backend.ps1

# окно 2 — frontend
.\scripts\dev-frontend.ps1
```

### Linux / macOS / Git Bash

```bash
# окно 1
bash scripts/dev-backend.sh

# окно 2
bash scripts/dev-frontend.sh
```

Скрипты сами создают venv, ставят зависимости, готовят `.env`, применяют
миграции и поднимают серверы с hot-reload. Фронт на http://localhost:5173,
Swagger на http://localhost:8000/docs.

### Тот же запуск вручную

```bash
cd backend
python -m venv venv
venv/Scripts/activate          # Linux/macOS: source venv/bin/activate
pip install -r requirements-dev.txt

# SQLite (по умолчанию, ничего поднимать не надо)
export DATABASE_URL="sqlite+aiosqlite:///./data/db.sqlite3"
# либо PostgreSQL:
# export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/livez"

alembic upgrade head
uvicorn app.main:app --reload
```

```bash
cd frontend
npm install
npm run dev
```

### Если нужен PostgreSQL локально

```bash
docker compose up -d db      # только БД
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/livez"
cd backend && alembic upgrade head && uvicorn app.main:app --reload
```

---

## Команды (Makefile)

```bash
make help              # список всех команд
make install           # venv + зависимости backend
make dev               # backend с hot-reload
make dev-frontend      # frontend
make migrate           # применить миграции
make migration m="..."  # создать миграцию
make test              # pytest
make lint              # ruff
make format            # автоформат
make typecheck         # mypy
make check             # lint + типы + тесты (то же, что в CI)
make up / make down    # Docker dev
make logs
make migrate-docker    # миграции внутри контейнера
```

---

## Миграции

После изменения моделей в `app/models.py`:

```bash
# локально
make migration m="добавил лайки"
make migrate

# в Docker
make migration-docker m="добавил лайки"
make migrate-docker
```

Проверить, что модели и миграции не разошлись:

```bash
cd backend && alembic check
```

Команда должна ответить `No new upgrade operations detected.` Это же
проверяется в CI и в тестах (`tests/test_migrations.py`).

---

## Тесты

```bash
make test
# или
cd backend && pytest -q
```

Тесты работают на SQLite в памяти и **не требуют** запущенного PostgreSQL.
Покрыто: регистрация и вход, смена ника/пароля, удаление аккаунта, CRUD постов,
пагинация, поиск, комментарии, подписки, группы, загрузка файлов, миграции.

---

## Переменные окружения

Все настройки описаны в `.env.example` соответствующих папок.

| Переменная | Где | Что |
|---|---|---|
| `SECRET_KEY` | backend/.env | секрет для JWT — обязательно случайный |
| `DATABASE_URL` | backend/.env | строка подключения (PostgreSQL или SQLite) |
| `CORS_ORIGINS` | backend/.env | список origin через запятую |
| `ACCESS_TOKEN_EXPIRE_SECONDS` | backend/.env | время жизни токена (по умолчанию 3600) |
| `COOKIE_SECURE` | backend/.env | `true` **только** при работе по HTTPS |
| `COOKIE_SAMESITE` | backend/.env | `lax` / `strict` / `none` |
| `MAX_UPLOAD_MB` / `MAX_AVATAR_MB` | backend/.env | лимиты размера файлов |
| `UPLOAD_DIR` | backend/.env | каталог загрузок (по умолчанию `uploads`) |
| `DEBUG` / `LOG_LEVEL` | backend/.env | подробность логов |
| `POSTGRES_*` | .env (корень) | креды БД для docker-compose |
| `VITE_BACKEND_URL` | frontend/.env.local | адрес backend для прокси Vite |

> **Важно про `COOKIE_SECURE`.** Если поставить `true`, а сайт открывается по
> HTTP, браузер не отправит cookie с токеном, и любой вход будет возвращать
> 401. Включайте этот флаг только вместе с HTTPS.

---

## Продакшн

```bash
cp .env.example .env
cp backend/.env.example backend/.env
# заполните .env и backend/.env

docker compose -f docker-compose.prod.yml up --build -d
```

Что меняется в проде:

- фронтенд собирается в статику и раздаётся **nginx** (с gzip и кешем ассетов);
- backend не публикуется наружу, доступ идёт через nginx;
- `DEBUG=false`, миграции применяются при старте контейнера;
- backend работает от непривилегированного пользователя.

Чеклист перед выкладкой:

- [ ] `SECRET_KEY` — случайный, не из примера
- [ ] `POSTGRES_PASSWORD` — сильный пароль
- [ ] `CORS_ORIGINS` — конкретный домен фронта, не `*`
- [ ] `COOKIE_SECURE=true` и сайт реально работает по HTTPS
- [ ] `DEBUG=false`
- [ ] Есть бэкап тома `postgres_data`
- [ ] HTTPS терминируется на nginx/Caddy перед приложением (FastAPI сам TLS не умеет)

---

## Архитектура

```
HTTP → router → service → repository → БД
        │         │          │
        │         │          └── flush(), без commit(): транзакция одна на запрос
        │         └── бизнес-правила, доменные исключения
        └── только валидация схем и вызов сервиса
```

- **Одна транзакция на HTTP-запрос.** `get_db()` коммитит в конце запроса,
  репозитории вызывают `flush()`. Любая ошибка откатывает запрос целиком.
- **Доменные исключения знают свой статус** (`app/exceptions.py`), обработчики
  в `app/handlers.py` превращают их в ответы. В роутерах нет `try/except`.
- **Загрузки проверяются по содержимому**, а не по заголовку `Content-Type`:
  подделанный MIME-тип не пройдёт (`app/utils/files.py`).
