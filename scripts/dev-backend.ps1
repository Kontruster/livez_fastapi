# LiveZ — локальный запуск backend без Docker (Windows PowerShell).
#
#   .\scripts\dev-backend.ps1            # поднять venv, миграции и uvicorn
#   .\scripts\dev-backend.ps1 -SkipInstall
#
# По умолчанию используется SQLite (файл backend/data/db.sqlite3) — PostgreSQL
# не нужен. Чтобы работать с PostgreSQL, задайте перед запуском:
#   $env:DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/livez"

param(
    [switch]$SkipInstall,
    [int]$Port = 8000
)

$ErrorActionPreference = 'Stop'

$backendDir = Split-Path -Parent $PSScriptRoot
Set-Location $backendDir

$venvPython = Join-Path $backendDir 'venv\Scripts\python.exe'

if (-not (Test-Path $venvPython)) {
    Write-Host '> Создаю виртуальное окружение...' -ForegroundColor Cyan
    python -m venv venv
}

if (-not $SkipInstall) {
    Write-Host '> Устанавливаю зависимости...' -ForegroundColor Cyan
    & $venvPython -m pip install --upgrade pip --quiet
    & $venvPython -m pip install -r requirements-dev.txt --quiet
}

# .env обязателен для запуска
$envFile = Join-Path $backendDir '.env'
if (-not (Test-Path $envFile)) {
    Write-Host '> backend\.env не найден, создаю из .env.example с локальными настройками' -ForegroundColor Yellow
    Copy-Item (Join-Path $backendDir '.env.example') $envFile

    $secret = & $venvPython -c "import secrets; print(secrets.token_urlsafe(64))"
    $content = Get-Content $envFile -Raw
    $content = $content -replace 'SECRET_KEY=.*', "SECRET_KEY=$secret"
    # локально по умолчанию — SQLite, чтобы не требовать поднятого PostgreSQL
    $content = $content -replace 'DATABASE_URL=.*', 'DATABASE_URL=sqlite+aiosqlite:///./data/db.sqlite3'
    Set-Content $envFile $content
}

if (-not $env:DATABASE_URL) {
    # если в .env прописан docker-хост "db", локально он недоступен
    $dbLine = Select-String -Path $envFile -Pattern '^DATABASE_URL=(.*)$' | Select-Object -First 1
    if ($dbLine -and $dbLine.Matches[0].Groups[1].Value -match '@db:') {
        Write-Host '> В .env указан хост "db" (Docker). Локально переключаюсь на SQLite.' -ForegroundColor Yellow
        $env:DATABASE_URL = 'sqlite+aiosqlite:///./data/db.sqlite3'
    }
}

New-Item -ItemType Directory -Force -Path (Join-Path $backendDir 'data') | Out-Null

Write-Host '> Применяю миграции...' -ForegroundColor Cyan
& $venvPython -m alembic upgrade head

Write-Host "> Backend: http://localhost:$Port  (Swagger: /docs)" -ForegroundColor Green
& $venvPython -m uvicorn app.main:app --reload --host 127.0.0.1 --port $Port
