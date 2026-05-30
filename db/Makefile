SHELL := /bin/bash

ROOT_DIR := ..
BACKEND_DIR := $(ROOT_DIR)/backend
ROOT_ENV_FILE := $(ROOT_DIR)/.env
BACKEND_ENV_FILE := $(BACKEND_DIR)/.env
TEST_SQL_DIR := tests
POSTGRES_CONTAINER ?= findoctor-postgres

ifneq (,$(wildcard $(ROOT_ENV_FILE)))
include $(ROOT_ENV_FILE)
export
endif

ifneq (,$(wildcard $(BACKEND_ENV_FILE)))
include $(BACKEND_ENV_FILE)
export
endif

POSTGRES_DB ?= findoctor
POSTGRES_USER ?= findoctor

PSQL := docker exec -i $(POSTGRES_CONTAINER) psql -v ON_ERROR_STOP=1 -U "$(POSTGRES_USER)" -d "$(POSTGRES_DB)"

.PHONY: help test-users-create test-users-delete test-users-reset test-users-list check-db

help:
	@echo "Команды для тестовых финансовых сценариев FinDoctor"
	@echo ""
	@echo "  make test-users-create    Загрузить 5 больших пользовательских сценариев"
	@echo "  make test-users-delete    Удалить этих пользователей и все их тестовые данные"
	@echo "  make test-users-reset     Удалить сценарии и загрузить их заново"
	@echo "  make test-users-list      Показать загруженных тестовых пользователей"

check-db:
	@docker ps --format '{{.Names}}' | grep -qx "$(POSTGRES_CONTAINER)" || { \
		echo "Контейнер Postgres '$(POSTGRES_CONTAINER)' не запущен."; \
		echo "Запустите его командой: make -C ../backend db-up && make -C ../backend migrate"; \
		exit 1; \
	}

test-users-create: check-db test-users-delete
	@echo "Загружаем большие финансовые тестовые сценарии в $(POSTGRES_DB)..."
	@$(PSQL) < "$(TEST_SQL_DIR)/seed_test_users.sql"

test-users-delete: check-db
	@echo "Удаляем финансовые тестовые сценарии из $(POSTGRES_DB)..."
	@$(PSQL) < "$(TEST_SQL_DIR)/delete_test_users.sql"

test-users-reset: test-users-create

test-users-list: check-db
	@$(PSQL) -c "SELECT email, first_name, last_name, base_currency, timezone, created_at FROM users WHERE email LIKE 'scenario.%@findoctor.test' ORDER BY email;"
