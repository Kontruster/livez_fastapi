#!/usr/bin/env bash
# LiveZ — локальный запуск backend без Docker (Linux / macOS / Git Bash).
#
#   bash scripts/dev-backend.sh
#
# По умолчанию используется SQLite (файл backend/data/db.sqlite3) — PostgreSQL
# не нужен. Чтобы работать с PostgreSQL, задайте перед запуском:
#   export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/livez"

set -euo pipefail

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/backend"
PORT="${PORT:-8000}"

cd "$BACKEND_DIR"

if [ ! -d venv ]; then
    echo "> Создаю виртуальное окружение..."
    python3 -m venv venv
fi

VENV_PY="$BACKEND_DIR/venv/bin/python"

echo "> Устанавливаю зависимости..."
"$VENV_PY" -m pip install --upgrade pip --quiet
"$VENV_PY" -m pip install -r requirements-dev.txt --quiet

if [ ! -f .env ]; then
    echo "> backend/.env не найден, создаю из .env.example с локальными настройками"
    cp .env.example .env
    SECRET="$("$VENV_PY" -c 'import secrets; print(secrets.token_urlsafe(64))')"
    # sed -i работает по-разному в GNU и BSD, поэтому пишем через временный файл
    sed -e "s|^SECRET_KEY=.*|SECRET_KEY=$SECRET|" \
        -e "s|^DATABASE_URL=.*|DATABASE_URL=sqlite+aiosqlite:///./data/db.sqlite3|" \
        .env > .env.tmp && mv .env.tmp .env
fi

if [ -z "${DATABASE_URL:-}" ] && grep -q '@db:' .env; then
    echo "> В .env указан хост \"db\" (Docker). Локально переключаюсь на SQLite."
    export DATABASE_URL="sqlite+aiosqlite:///./data/db.sqlite3"
fi

mkdir -p data

echo "> Применяю миграции..."
"$VENV_PY" -m alembic upgrade head

echo "> Backend: http://localhost:$PORT  (Swagger: /docs)"
exec "$VENV_PY" -m uvicorn app.main:app --reload --host 127.0.0.1 --port "$PORT"
