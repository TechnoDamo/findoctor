SHELL := /bin/bash
export PATH := /opt/local/bin:$(PATH)

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

.PHONY: help init deploy-local deploy-cloud stop status logs shell test-users-create test-users-delete test-users-reset test-users-list check-db

help:
	@echo "Команды для тестовых финансовых сценариев FinDoctor"
	@echo ""
	@echo "  make init                 Подготовить backend env для локальной БД"
	@echo "  make deploy-local         Запустить локальный PostgreSQL и применить миграции"
	@echo "  make deploy-cloud         Проверить cloud DATABASE_URL"
	@echo "  make stop                 Остановить локальный PostgreSQL"
	@echo "  make status               Показать статус PostgreSQL container"
	@echo "  make logs                 Смотреть логи PostgreSQL"
	@echo ""
	@echo "  make test-users-create    Загрузить 5 больших пользовательских сценариев"
	@echo "  make test-users-delete    Удалить этих пользователей и все их тестовые данные"
	@echo "  make test-users-reset     Удалить сценарии и загрузить их заново"
	@echo "  make test-users-list      Показать загруженных тестовых пользователей"

init:
	$(MAKE) -C $(BACKEND_DIR) init-env

deploy-local: init
	$(MAKE) -C $(BACKEND_DIR) db-up
	@echo "Waiting for PostgreSQL..."
	@for i in $$(seq 1 30); do \
		if docker exec $(POSTGRES_CONTAINER) pg_isready -U "$(POSTGRES_USER)" -d "$(POSTGRES_DB)" >/dev/null 2>&1; then \
			echo "PostgreSQL is ready"; break; \
		fi; \
		sleep 1; \
	done
	$(MAKE) -C $(BACKEND_DIR) migrate

deploy-cloud:
	@test -n "$(DATABASE_URL)" || { echo "DATABASE_URL не задан"; exit 1; }
	@if echo "$(DATABASE_URL)" | grep -Eq '@(localhost|127\.0\.0\.1|host\.docker\.internal)'; then \
		echo "DATABASE_URL похож на локальный адрес, а DEPLOYMENT=cloud ожидает managed/external PostgreSQL."; \
		exit 1; \
	fi
	@echo "Cloud PostgreSQL config OK: DATABASE_URL задан и не выглядит локальным."

stop:
	$(MAKE) -C $(BACKEND_DIR) db-stop

status:
	@docker ps -a --filter "name=$(POSTGRES_CONTAINER)" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

logs:
	$(MAKE) -C $(BACKEND_DIR) db-logs

shell:
	$(MAKE) -C $(BACKEND_DIR) db-psql

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
