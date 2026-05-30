SHELL := /bin/bash
UV ?= $(shell command -v uv 2>/dev/null || echo /Users/damir/.langflow/uv/uv)

ROOT_DIR := ..
ROOT_ENV_FILE := $(ROOT_DIR)/.env
ENV_FILE := .env

ifneq (,$(wildcard $(ROOT_ENV_FILE)))
include $(ROOT_ENV_FILE)
export
endif

ifneq (,$(wildcard $(ENV_FILE)))
include $(ENV_FILE)
export
endif

APP_HOST ?= 0.0.0.0
APP_PORT ?= 8000
POSTGRES_PORT ?= 5432
DATABASE_URL ?= postgresql+psycopg://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@localhost:$(POSTGRES_PORT)/$(POSTGRES_DB)

.PHONY: help db-up db-start db-stop db-logs db-psql migrate migration rollback db-current db-history run test test-unit test-auth test-accounts test-comprehensive test-all test-verbose test-debug test-coverage lint compile contract-check test-db-reset

help:
	@echo "Commands:"
	@echo ""
	@echo "  Application:"
	@echo "    make run                  Start FastAPI dev server on $(APP_HOST):$(APP_PORT)"
	@echo ""
	@echo "  Database:"
	@echo "    make db-up                Start local PostgreSQL container"
	@echo "    make db-start             Start existing PostgreSQL container"
	@echo "    make db-stop              Stop PostgreSQL container"
	@echo "    make db-logs              Follow PostgreSQL logs"
	@echo "    make db-psql              Open psql inside the container"
	@echo ""
	@echo "  Migrations:"
	@echo "    make migrate              Apply all migrations"
	@echo "    make migration m='msg'    Create empty Alembic migration"
	@echo "    make rollback             Roll back one migration"
	@echo "    make db-current           Show current Alembic revision"
	@echo "    make db-history           Show Alembic migration history"
	@echo ""
	@echo "  Testing:"
	@echo "    make test                 Run full local test gate"
	@echo "    make test-unit            Run pytest only"
	@echo "    make test-auth           Run authentication tests only"
	@echo "    make test-accounts       Run accounts tests only"
	@echo "    make test-comprehensive  Run comprehensive tests with database verification"
	@echo "    make test-all            Run all tests including comprehensive ones"
	@echo "    make test-verbose        Run tests with verbose output"
	@echo "    make test-debug          Run tests with debug output"
	@echo "    make test-coverage       Run tests with coverage report"
	@echo "    make lint                Run ruff linter"
	@echo "    make compile             Compile Python files"
	@echo "    make contract-check      Check FastAPI routes against OpenAPI contract"

db-up:
	mkdir -p $(ROOT_DIR)/db/postgres-data
	@if docker ps -a --format '{{.Names}}' | grep -qx 'findoctor-postgres'; then \
		docker start findoctor-postgres; \
	else \
		docker run -d \
			--name findoctor-postgres \
			--env-file $(ENV_FILE) \
			-p "$(POSTGRES_PORT):5432" \
			-v "$$(cd $(ROOT_DIR) && pwd)/db/postgres-data:/var/lib/postgresql/data" \
			postgres:16-alpine; \
	fi

db-start:
	docker start findoctor-postgres

db-stop:
	docker stop findoctor-postgres

db-logs:
	docker logs -f findoctor-postgres

db-psql:
	docker exec -it findoctor-postgres psql -U "$(POSTGRES_USER)" -d "$(POSTGRES_DB)"

migrate:
	DATABASE_URL="$(DATABASE_URL)" $(UV) run alembic upgrade head

migration:
	@test -n "$(m)" || (echo "Usage: make migration m='create table name'" && exit 1)
	DATABASE_URL="$(DATABASE_URL)" $(UV) run alembic revision -m "$(m)"

rollback:
	DATABASE_URL="$(DATABASE_URL)" $(UV) run alembic downgrade -1

db-current:
	DATABASE_URL="$(DATABASE_URL)" $(UV) run alembic current

db-history:
	DATABASE_URL="$(DATABASE_URL)" $(UV) run alembic history

run:
	@echo "Starting on http://$(APP_HOST):$(APP_PORT)"
	$(UV) run uvicorn app.main:app --host $(APP_HOST) --port $(APP_PORT) --reload

test:
	$(MAKE) lint
	$(MAKE) compile
	$(MAKE) test-db-reset
	$(MAKE) test-unit

test-unit:
	$(UV) run pytest tests/ -v

test-auth:
	$(MAKE) test-db-reset
	$(UV) run pytest tests/test_auth.py tests/test_auth_comprehensive.py -v

test-accounts:
	$(MAKE) test-db-reset
	$(UV) run pytest tests/test_accounts.py -v

test-comprehensive:
	$(MAKE) test-db-reset
	$(UV) run pytest tests/test_auth_comprehensive.py -v

test-all:
	$(MAKE) test

test-verbose:
	$(UV) run pytest tests/ -vv

test-debug:
	$(UV) run pytest tests/ -vvv --capture=no

test-coverage:
	$(MAKE) test-db-reset
	$(UV) run pytest tests/ --cov=app --cov-report=html --cov-report=term

lint:
	$(UV) run ruff check app tests scripts

compile:
	$(UV) run python -m compileall -q app tests scripts

contract-check:
	$(UV) run pytest tests/test_openapi_contract.py -v

test-db-reset:
	$(UV) run python scripts/reset_test_db.py
