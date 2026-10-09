# LiveZ — локальный запуск frontend без Docker (Windows PowerShell).
#
#   .\scripts\dev-frontend.ps1
#
# Vite проксирует /auth, /posts, /users и т.д. на backend (по умолчанию
# http://127.0.0.1:8000 — то есть на dev-backend.ps1).

param(
    [int]$Port = 5173,
    [string]$BackendUrl = 'http://127.0.0.1:8000'
)

$ErrorActionPreference = 'Stop'

$frontendDir = Join-Path (Split-Path -Parent $PSScriptRoot) 'frontend'
Set-Location $frontendDir

if (-not (Test-Path (Join-Path $frontendDir 'node_modules'))) {
    Write-Host '> Устанавливаю зависимости...' -ForegroundColor Cyan
    npm install
}

if (-not (Test-Path (Join-Path $frontendDir '.env.local'))) {
    Write-Host '> Создаю frontend\.env.local' -ForegroundColor Cyan
    "VITE_BACKEND_URL=$BackendUrl`nVITE_PORT=$Port" |
        Set-Content (Join-Path $frontendDir '.env.local')
}

Write-Host "> Frontend: http://localhost:$Port  (backend: $BackendUrl)" -ForegroundColor Green
$env:VITE_BACKEND_URL = $BackendUrl
npm run dev -- --host 127.0.0.1 --port $Port
