SHELL := /bin/bash

ENV_FILE ?= .env

ifneq (,$(wildcard $(ENV_FILE)))
include $(ENV_FILE)
export
endif

TEI_IMAGE ?= ghcr.io/huggingface/text-embeddings-inference:cpu-1.9
TEI_CONTAINER_NAME ?= tei-findoctor
TEI_HOST ?= 0.0.0.0
TEI_PORT ?= 8200
TEI_BASE_URL ?= http://localhost:$(TEI_PORT)
TEI_MODEL_ID ?= BAAI/bge-m3
TEI_REVISION ?=
TEI_MODELS_DIR ?= ./models
TEI_MAX_CLIENT_BATCH_SIZE ?= 32
TEI_MAX_BATCH_TOKENS ?= 16384
TEI_POOLING ?=

MODELS_DIR_ABS := $(abspath $(TEI_MODELS_DIR))

.PHONY: help init pull run stop restart logs shell ps wait info test test-health test-embed test-openai test-similarity curl-examples clean clean-all

help:
	@echo "TEI — локальный embedding inference service ФинДоктора"
	@echo ""
	@echo "  make init           Создать .env"
	@echo "  make pull           Скачать Docker image"
	@echo "  make run            Запустить TEI на $(TEI_BASE_URL)"
	@echo "  make stop           Остановить и удалить контейнер"
	@echo "  make restart        Перезапустить контейнер"
	@echo "  make logs           Смотреть логи"
	@echo "  make shell          Открыть shell в контейнере"
	@echo "  make ps             Показать статус контейнера"
	@echo "  make wait           Дождаться /health"
	@echo "  make info           Показать /info"
	@echo "  make test           Запустить health + embeddings smoke tests"
	@echo "  make curl-examples  Показать готовые curl-примеры"
	@echo "  make clean-all      Остановить контейнер и удалить model cache"
	@echo ""
	@echo "Быстрый старт:"
	@echo "  make init && make pull && make run && make test"

init:
	@test -f .env || cp .env.example .env
	@mkdir -p "$(MODELS_DIR_ABS)"
	@echo "tei/.env готов"

pull:
	docker pull "$(TEI_IMAGE)"

run:
	@if docker ps -a --format '{{.Names}}' | grep -qx '$(TEI_CONTAINER_NAME)'; then \
		echo "Контейнер $(TEI_CONTAINER_NAME) уже существует. Используйте make restart или make stop."; \
		exit 1; \
	fi
	@mkdir -p "$(MODELS_DIR_ABS)"
	docker run -d \
		--name "$(TEI_CONTAINER_NAME)" \
		-p "$(TEI_PORT):80" \
		-v "$(MODELS_DIR_ABS):/data" \
		"$(TEI_IMAGE)" \
		--model-id "$(TEI_MODEL_ID)" \
		$(if $(TEI_REVISION),--revision "$(TEI_REVISION)",) \
		--max-client-batch-size "$(TEI_MAX_CLIENT_BATCH_SIZE)" \
		--max-batch-tokens "$(TEI_MAX_BATCH_TOKENS)" \
		$(if $(TEI_POOLING),--pooling "$(TEI_POOLING)",)
	@echo "TEI запущен на $(TEI_BASE_URL)"
	@echo "Model: $(TEI_MODEL_ID)"

stop:
	-docker stop "$(TEI_CONTAINER_NAME)" 2>/dev/null
	-docker rm "$(TEI_CONTAINER_NAME)" 2>/dev/null

restart:
	$(MAKE) stop
	$(MAKE) run

logs:
	docker logs -f "$(TEI_CONTAINER_NAME)"

shell:
	docker exec -it "$(TEI_CONTAINER_NAME)" sh

ps:
	docker ps -a --filter "name=$(TEI_CONTAINER_NAME)" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

wait:
	@./scripts/wait_for_tei.sh

info:
	@curl -sS "$(TEI_BASE_URL)/info" | python3 -m json.tool

test: test-health test-embed test-openai test-similarity

test-health:
	@./scripts/wait_for_tei.sh

test-embed:
	@./scripts/test_embed.sh

test-openai:
	@./scripts/test_openai_embeddings.sh

test-similarity:
	@./scripts/test_similarity.sh

curl-examples:
	@./scripts/print_curl_examples.sh

clean: stop

clean-all: stop
	rm -rf "$(MODELS_DIR_ABS)"
