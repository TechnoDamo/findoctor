SHELL := /bin/bash

ENV_FILE ?= .env

ifneq (,$(wildcard $(ENV_FILE)))
include $(ENV_FILE)
export
endif

RAGFLOW_REPO_URL   ?= https://github.com/infiniflow/ragflow.git
RAGFLOW_RUNTIME_DIR ?= .runtime/ragflow
RAGFLOW_GIT_REF     ?= main
RAGFLOW_BASE_URL    ?= http://localhost:9380

UPSTREAM_DOCKER_DIR := $(RAGFLOW_RUNTIME_DIR)/docker
UPSTREAM_ENV        := $(UPSTREAM_DOCKER_DIR)/.env

.PHONY: help init fetch configure pull up down stop start reload restart wait test \
        key-create key-list key-delete ds-create ds-list ds-delete \
        load-test-docs clear-dataset docs-list setup

help:
	@echo "RAGFlow — self-hosted RAG-сервис ФинДоктора"
	@echo ""
	@echo "Настройка:"
	@echo "  make init         Создать .env из .env.example"
	@echo "  make fetch        Клонировать upstream RAGFlow в $(RAGFLOW_RUNTIME_DIR)"
	@echo "  make configure    Подготовить upstream docker/.env из шаблона"
	@echo "  make pull         Скачать все Docker-образы (docker compose pull)"
	@echo "  make test          Проверить API: health + векторный поиск + LLM-ретривал"
	@echo ""
	@echo "Управление контейнерами:"
	@echo "  make up           Создать и запустить все контейнеры (docker compose up -d)"
	@echo "  make down         Остановить и удалить контейнеры + сети (docker compose down)"
	@echo "  make stop         Приостановить контейнеры без удаления (docker compose stop)"
	@echo "  make start        Возобновить остановленные контейнеры (docker compose start)"
	@echo "  make reload       Пересоздать контейнеры заново (docker compose up -d --force-recreate)"
	@echo "  make restart      Перезапустить существующие контейнеры (docker compose restart)"
	@echo "  make wait         Дождаться HTTP-ответа RAGFlow"
	@echo ""
	@echo "Различия:"
	@echo "  stop  сохраняет контейнеры и тома на диске, down — удаляет."
	@echo "  start возобновляет stop-нутые контейнеры, up — создаёт заново."
	@echo "  reload пересоздаёт контейнеры (сброс состояния), restart перезапускает на месте."
	@echo ""
	@echo "Быстрый старт (всё одной командой):"
	@echo "  make up && make setup           Запустить RAGFlow и настроить admin + API-ключ + датасет + модели"
	@echo "  make load-test-docs             Загрузить 18 тестовых документов (опционально)"
	@echo "  make test                       Проверить, что retrieval работает"
	@echo ""
	@echo "Управление API-ключами (требует RAGFLOW_ADMIN_EMAIL/PASSWORD):"
	@echo "  make key-create NAME=<name>     Создать API-ключ и записать в RAGFLOW_API_KEY"
	@echo "  make key-list                   Показать все API-ключи"
	@echo "  make key-delete TOKEN=<token>   Удалить API-ключ"
	@echo ""
	@echo "Управление датасетами (требует RAGFLOW_ADMIN_EMAIL/PASSWORD):"
	@echo "  make ds-create NAME=<name>      Создать датасет и записать в RAGFLOW_DATASET_ID"
	@echo "  make ds-list                    Показать все датасеты"
	@echo "  make ds-delete ID=<dataset_id>  Удалить датасет"
	@echo ""
	@echo "Тестовые документы:"
	@echo "  make load-test-docs             Загрузить тестовые документы в датасет и запустить парсинг"
	@echo "  make clear-dataset              Удалить все документы из датасета"
	@echo "  make docs-list                  Список документов со статусом индексации"
	@echo ""
	@echo "Авто-настройка:"
	@echo "  make setup                      Полная настройка RAGFlow: admin, API-ключ, датасет, модели"

# ----------------------------------------------------------------------
# Настройка
# ----------------------------------------------------------------------
init:
	@test -f .env || cp .env.example .env
	@test -f allowed_resources.txt || touch allowed_resources.txt
	@echo "ragflow/.env готов. Заполните RAGFLOW_API_KEY и RAGFLOW_DATASET_ID после настройки RAGFlow."

fetch:
	@if [ -d "$(RAGFLOW_RUNTIME_DIR)/.git" ]; then \
		echo "Upstream RAGFlow уже клонирован: $(RAGFLOW_RUNTIME_DIR)"; \
	else \
		mkdir -p "$$(dirname "$(RAGFLOW_RUNTIME_DIR)")"; \
		git clone "$(RAGFLOW_REPO_URL)" "$(RAGFLOW_RUNTIME_DIR)"; \
	fi
	@cd "$(RAGFLOW_RUNTIME_DIR)" && git fetch --tags origin && git checkout "$(RAGFLOW_GIT_REF)"

configure:
	@test -d "$(UPSTREAM_DOCKER_DIR)" || { echo "Каталог upstream docker не найден. Сначала: make fetch"; exit 1; }
	@./scripts/configure_upstream_env.sh "$(UPSTREAM_DOCKER_DIR)" "$(UPSTREAM_ENV)"

pull: _compose_check
	cd "$(UPSTREAM_DOCKER_DIR)" && docker compose pull
	@echo "Образы RAGFlow скачаны."

# ----------------------------------------------------------------------
# Управление контейнерами
# ----------------------------------------------------------------------
_compose_check:
	@test -f "$(UPSTREAM_DOCKER_DIR)/docker-compose.yml" || { echo "Upstream compose-файл не найден. Сначала: make fetch && make configure"; exit 1; }

up: _compose_check
	cd "$(UPSTREAM_DOCKER_DIR)" && docker compose up -d
	@echo "RAGFlow запущен на $(RAGFLOW_BASE_URL)"

down: _compose_check
	cd "$(UPSTREAM_DOCKER_DIR)" && docker compose down
	@echo "RAGFlow остановлен, контейнеры и сети удалены."

stop: _compose_check
	cd "$(UPSTREAM_DOCKER_DIR)" && docker compose stop
	@echo "RAGFlow приостановлен. Контейнеры сохранены. Возобновить: make start"

start: _compose_check
	cd "$(UPSTREAM_DOCKER_DIR)" && docker compose start
	@echo "RAGFlow возобновлён на $(RAGFLOW_BASE_URL)"

reload: _compose_check
	cd "$(UPSTREAM_DOCKER_DIR)" && docker compose up -d --force-recreate
	@echo "RAGFlow пересоздан на $(RAGFLOW_BASE_URL)"

restart: _compose_check
	cd "$(UPSTREAM_DOCKER_DIR)" && docker compose restart
	@echo "RAGFlow перезапущен на $(RAGFLOW_BASE_URL)"

wait:
	@for i in {1..120}; do \
		status=$$(curl -sS -o /dev/null -w '%{http_code}' --max-time 5 "$(RAGFLOW_BASE_URL)/api/v1/" || true); \
		if [[ "$$status" == "200" || "$$status" == "404" ]]; then \
			echo "RAGFlow is ready at $(RAGFLOW_BASE_URL)"; \
			exit 0; \
		fi; \
		sleep 2; \
	done; \
	echo "RAGFlow was not ready at $(RAGFLOW_BASE_URL)"; \
	exit 1

# ----------------------------------------------------------------------
# Тесты
# ----------------------------------------------------------------------
_api_check:
	@if [ -z "$${RAGFLOW_API_KEY:-}" ]; then echo "RAGFLOW_API_KEY не задан в .env. Заполните после настройки RAGFlow."; exit 1; fi
	@if [ -z "$${RAGFLOW_DATASET_ID:-}" ]; then echo "RAGFLOW_DATASET_ID не задан в .env. Заполните после настройки RAGFlow."; exit 1; fi

test: _api_check
	@echo "=== 1. Health-чек RAGFlow ==="
	@STATUS=$$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$(RAGFLOW_BASE_URL)/api/v1/"); \
	if [ "$$STATUS" != "200" ] && [ "$$STATUS" != "404" ]; then \
		echo "FAIL: статус $$STATUS, сервер недоступен на $(RAGFLOW_BASE_URL)"; exit 1; \
	fi; \
	echo "OK: сервер отвечает (статус $$STATUS)"
	@echo ""
	@echo "=== 2. Векторный поиск (без LLM-переранжирования) ==="
	@RESPONSE=$$(curl -sS --max-time 30 \
		-X POST "$(RAGFLOW_BASE_URL)/api/v1/datasets/$$RAGFLOW_DATASET_ID/search" \
		-H "Authorization: Bearer $$RAGFLOW_API_KEY" \
		-H "Content-Type: application/json" \
		-d '{"question":"emergency fund size","page":1,"size":3,"similarity_threshold":0.2,"vector_similarity_weight":0.3}'); \
	echo "$$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$$RESPONSE"; \
	if echo "$$RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d.get('code')==0, d" 2>/dev/null; then \
		echo "OK: векторный поиск отработал"; \
	else \
		echo "WARN: проверьте ответ выше — возможно, датасет пуст или не проиндексирован"; \
	fi
	@echo ""
	@echo "=== 3. LLM-ретривал (с RAG-переранжированием) ==="
	@RESPONSE=$$(curl -sS --max-time 30 \
		-X POST "$(RAGFLOW_BASE_URL)/api/v1/retrieval" \
		-H "Authorization: Bearer $$RAGFLOW_API_KEY" \
		-H "Content-Type: application/json" \
		-d '{"question":"emergency fund size","dataset_ids":["'"$$RAGFLOW_DATASET_ID"'"],"page":1,"page_size":3}'); \
	echo "$$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$$RESPONSE"; \
	if echo "$$RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d.get('code')==0, d" 2>/dev/null; then \
		echo "OK: retrieval отработал успешно"; \
	else \
		echo "WARN: проверьте ответ выше — возможно, датасет пуст или не проиндексирован"; \
	fi

# ----------------------------------------------------------------------
# Административные API-команды (требуют RAGFLOW_ADMIN_EMAIL/PASSWORD)
# ----------------------------------------------------------------------
_admin_check:
	@if [ -z "$${RAGFLOW_ADMIN_EMAIL:-}" ]; then echo "RAGFLOW_ADMIN_EMAIL не задан в .env"; exit 1; fi
	@if [ -z "$${RAGFLOW_ADMIN_PASSWORD:-}" ]; then echo "RAGFLOW_ADMIN_PASSWORD не задан в .env"; exit 1; fi

# Внутренний хелпер: логин через cookie-based auth
_ragflow_login: _admin_check
	@python3 scripts/ragflow_admin.py key-list >/dev/null 2>&1

# -- API-ключи ----------------------------------------------------------
key-create: _admin_check
	@python3 scripts/ragflow_admin.py key-create --name="$${NAME:-findoctor-backend}"

key-list: _admin_check
	@python3 scripts/ragflow_admin.py key-list

key-delete: _admin_check
	@if [ -z "$${TOKEN:-}" ]; then echo "Укажите TOKEN=<значение_ключа>"; exit 1; fi
	@python3 scripts/ragflow_admin.py key-delete --token="$$TOKEN"

# -- Датасеты ------------------------------------------------------------
ds-create: _admin_check
	@python3 scripts/ragflow_admin.py ds-create --name="$${NAME:-findoctor-recommendations}"

ds-list: _admin_check
	@python3 scripts/ragflow_admin.py ds-list

ds-delete: _admin_check
	@if [ -z "$${ID:-}" ]; then echo "Укажите ID=<dataset_id>"; exit 1; fi
	@python3 scripts/ragflow_admin.py ds-delete --id="$$ID"

# -- Тестовые документы --------------------------------------------------
load-test-docs: _admin_check up
	@bash scripts/load_test_docs.sh

clear-dataset: _admin_check up
	@bash scripts/clear_dataset.sh

# -- Список документов ---------------------------------------------------
docs-list: _api_check
	@python3 scripts/list_docs.py

# -- Полная авто-настройка -----------------------------------------------
setup: _admin_check
	@python3 scripts/setup_ragflow.py
