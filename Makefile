# LiveZ — команды разработки.
# Все цели работают и в Docker, и локально. Локальные используют venv.
#
# Быстрый старт:
#   make install     — поднять venv и поставить зависимости
#   make migrate     — применить миграции
#   make dev         — запустить бэкенд + фронтенд локально
#
# Docker:
#   make up / make down / make logs / make migrate-docker

.DEFAULT_GOAL := help
SHELL := /bin/bash

BACKEND_DIR := backend
FRONTEND_DIR := frontend

# Путь к python внутри venv (Windows и Unix)
ifeq ($(OS),Windows_NT)
  PYTHON   := python
  VENV_PY  := $(BACKEND_DIR)/venv/Scripts/python.exe
  VENV_PIP := $(VENV_PY) -m pip
else
  PYTHON   := python3
  VENV_PY  := $(BACKEND_DIR)/venv/bin/python
  VENV_PIP := $(VENV_PY) -m pip
endif

.PHONY: help
help: ## Показать список команд
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ---------- Локальная разработка ----------

.PHONY: venv
venv: ## Создать виртуальное окружение backend
	$(PYTHON) -m venv $(BACKEND_DIR)/venv

.PHONY: install
install: venv ## Поставить зависимости backend (включая dev)
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r $(BACKEND_DIR)/requirements-dev.txt

.PHONY: install-frontend
install-frontend: ## Поставить зависимости frontend
	cd $(FRONTEND_DIR) && npm install

.PHONY: migrate
migrate: ## Применить миграции к локальной БД
	cd $(BACKEND_DIR) && ../$(VENV_PY) -m alembic upgrade head

.PHONY: migration
migration: ## Создать миграцию: make migration m="описание"
	cd $(BACKEND_DIR) && ../$(VENV_PY) -m alembic revision --autogenerate -m "$(m)"

.PHONY: dev
dev: ## Запустить backend (uvicorn --reload)
	cd $(BACKEND_DIR) && ../$(VENV_PY) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: dev-frontend
dev-frontend: ## Запустить frontend (vite)
	cd $(FRONTEND_DIR) && npm run dev

# ---------- Качество кода ----------

.PHONY: test
test: ## Прогнать тесты
	cd $(BACKEND_DIR) && ../$(VENV_PY) -m pytest

.PHONY: test-cov
test-cov: ## Тесты с покрытием
	cd $(BACKEND_DIR) && ../$(VENV_PY) -m pytest --cov=app --cov-report=term-missing

.PHONY: lint
lint: ## Проверить backend линтером
	cd $(BACKEND_DIR) && ../$(VENV_PY) -m ruff check .

.PHONY: format
format: ## Отформатировать backend
	cd $(BACKEND_DIR) && ../$(VENV_PY) -m ruff format .
	cd $(BACKEND_DIR) && ../$(VENV_PY) -m ruff check --fix .

.PHONY: typecheck
typecheck: ## Проверить типы backend
	cd $(BACKEND_DIR) && ../$(VENV_PY) -m mypy app

.PHONY: lint-frontend
lint-frontend: ## Проверить frontend
	cd $(FRONTEND_DIR) && npm run lint

.PHONY: check
check: lint typecheck test ## Всё, что гоняет CI

# ---------- Docker ----------

.PHONY: up
up: ## Поднять все сервисы в Docker
	docker compose up --build -d

.PHONY: down
down: ## Остановить сервисы
	docker compose down

.PHONY: logs
logs: ## Логи всех сервисов
	docker compose logs -f

.PHONY: migrate-docker
migrate-docker: ## Применить миграции внутри контейнера
	docker compose exec backend alembic upgrade head

.PHONY: migration-docker
migration-docker: ## Создать миграцию в контейнере: make migration-docker m="описание"
	docker compose exec backend alembic revision --autogenerate -m "$(m)"

.PHONY: test-docker
test-docker: ## Прогнать тесты в контейнере
	docker compose exec backend pytest

.PHONY: sh
sh: ## Shell внутри backend-контейнера
	docker compose exec backend bash

.PHONY: clean
clean: ## Удалить кеши Python
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +
	find . -type d -name .ruff_cache -prune -exec rm -rf {} +
	find . -type d -name .mypy_cache -prune -exec rm -rf {} +
