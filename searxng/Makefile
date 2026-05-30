SHELL := /bin/bash

ENV_FILE ?= .env

ifneq (,$(wildcard $(ENV_FILE)))
include $(ENV_FILE)
export
endif

SEARXNG_IMAGE ?= searxng/searxng:latest
SEARXNG_CONTAINER_NAME ?= searxng-findoctor
SEARXNG_HOST ?= 0.0.0.0
SEARXNG_PORT ?= 8201
SEARXNG_BASE_URL ?= http://localhost:$(SEARXNG_PORT)
SEARXNG_SECRET_KEY ?= change-me-generate-with-openssl-rand-hex-32
SEARXNG_REQUEST_TIMEOUT ?= 10
SEARXNG_TEST_QUERY ?= site:cbr.ru key rate

CONFIG_DIR := $(abspath config)
SETTINGS_FILE := config/settings.yml

.PHONY: help init render-config pull run stop restart logs shell ps wait test test-json test-allowed curl-examples clean

help:
	@echo "SearXNG — внутренний self-hosted search-сервис ФинДоктора"
	@echo ""
	@echo "  make init           Создать .env и сгенерировать SEARXNG_SECRET_KEY при необходимости"
	@echo "  make pull           Скачать Docker image"
	@echo "  make run            Запустить SearXNG на $(SEARXNG_BASE_URL)"
	@echo "  make stop           Остановить и удалить контейнер"
	@echo "  make restart        Перезапустить контейнер"
	@echo "  make logs           Смотреть логи"
	@echo "  make shell          Открыть shell в контейнере"
	@echo "  make ps             Показать статус контейнера"
	@echo "  make wait           Дождаться доступности HTTP endpoint"
	@echo "  make test           Запустить JSON search smoke tests"
	@echo "  make curl-examples  Показать готовые curl-примеры"
	@echo ""
	@echo "Быстрый старт:"
	@echo "  make init && make pull && make run && make test"

init:
	@test -f .env || cp .env.example .env
	@if grep -q 'change-me-generate-with-openssl-rand-hex-32' .env; then \
		if command -v openssl >/dev/null 2>&1; then \
			key=$$(openssl rand -hex 32); \
			sed -i.bak "s/change-me-generate-with-openssl-rand-hex-32/$$key/g" .env; \
			rm -f .env.bak; \
			echo "SEARXNG_SECRET_KEY сгенерирован"; \
		else \
			echo "openssl не найден; отредактируйте SEARXNG_SECRET_KEY вручную"; \
		fi; \
	fi
	@$(MAKE) render-config
	@echo "searxng/.env готов"

render-config:
	@./scripts/render_config.sh

pull:
	docker pull "$(SEARXNG_IMAGE)"

run:
	@test -f "$(SETTINGS_FILE)" || { echo "Нет $(SETTINGS_FILE). Сначала запустите make init."; exit 1; }
	@if docker ps -a --format '{{.Names}}' | grep -qx '$(SEARXNG_CONTAINER_NAME)'; then \
		echo "Контейнер $(SEARXNG_CONTAINER_NAME) уже существует. Используйте make restart или make stop."; \
		exit 1; \
	fi
	docker run -d \
		--name "$(SEARXNG_CONTAINER_NAME)" \
		-p "$(SEARXNG_PORT):8080" \
		-e "SEARXNG_SECRET_KEY=$(SEARXNG_SECRET_KEY)" \
		-e "SEARXNG_REQUEST_TIMEOUT=$(SEARXNG_REQUEST_TIMEOUT)" \
		-v "$(CONFIG_DIR):/etc/searxng:ro" \
		"$(SEARXNG_IMAGE)"
	@echo "SearXNG запущен на $(SEARXNG_BASE_URL)"

stop:
	-docker stop "$(SEARXNG_CONTAINER_NAME)" 2>/dev/null
	-docker rm "$(SEARXNG_CONTAINER_NAME)" 2>/dev/null

restart:
	$(MAKE) stop
	$(MAKE) run

logs:
	docker logs -f "$(SEARXNG_CONTAINER_NAME)"

shell:
	docker exec -it "$(SEARXNG_CONTAINER_NAME)" sh

ps:
	docker ps -a --filter "name=$(SEARXNG_CONTAINER_NAME)" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

wait:
	@./scripts/wait_for_searxng.sh

test: test-json test-allowed

test-json:
	@./scripts/test_json_search.sh

test-allowed:
	@./scripts/test_allowed_query.sh

curl-examples:
	@./scripts/print_curl_examples.sh

clean: stop
