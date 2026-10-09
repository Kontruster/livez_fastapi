#!/usr/bin/env bash
# LiveZ — локальный запуск frontend без Docker (Linux / macOS / Git Bash).
#
#   bash scripts/dev-frontend.sh
#
# Vite проксирует /auth, /posts, /users и т.д. на backend (по умолчанию
# http://127.0.0.1:8000 — то есть на dev-backend.sh).

set -euo pipefail

FRONTEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/frontend"
PORT="${PORT:-5173}"
BACKEND_URL="${VITE_BACKEND_URL:-http://127.0.0.1:8000}"

cd "$FRONTEND_DIR"

if [ ! -d node_modules ]; then
    echo "> Устанавливаю зависимости..."
    npm install
fi

if [ ! -f .env.local ]; then
    echo "> Создаю frontend/.env.local"
    printf 'VITE_BACKEND_URL=%s\nVITE_PORT=%s\n' "$BACKEND_URL" "$PORT" > .env.local
fi

echo "> Frontend: http://localhost:$PORT  (backend: $BACKEND_URL)"
VITE_BACKEND_URL="$BACKEND_URL" exec npm run dev -- --host 127.0.0.1 --port "$PORT"
