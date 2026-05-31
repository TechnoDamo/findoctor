SHELL := /bin/bash

ROOT_DIR := $(CURDIR)

BACKEND_DIR := backend
FRONTEND_DIR := frontend
RAGFLOW_DIR := ragflow
SEARXNG_DIR := searxng
TEI_DIR := tei
VLLM_DIR := vLLM
GRAYLOG_DIR := graylog
WHISPER_DIR := whisper-server
DOCKER_COMPOSE ?= docker compose
COMPOSE_FILE ?= docker-compose.yml

BACKEND_PYTEST := $(if $(wildcard $(BACKEND_DIR)/.venv/bin/pytest),./.venv/bin/pytest,pytest)
BACKEND_RUFF := $(if $(wildcard $(BACKEND_DIR)/.venv/bin/ruff),./.venv/bin/ruff,ruff)
BACKEND_PYTHON := $(if $(wildcard $(BACKEND_DIR)/.venv/bin/python),./.venv/bin/python,python3)

.PHONY: help
.PHONY: init init-core init-recommendations init-observability init-voice
.PHONY: pull pull-recommendations pull-ai-local
.PHONY: local-up local-up-core local-up-recommendations local-up-ai local-down local-down-recommendations
.PHONY: compose-build compose-up-core compose-up-app compose-down compose-logs compose-ps
.PHONY: deploy-local-core deploy-local-rag deploy-local-ai deploy-hybrid-llm-local-rag deploy-cloud-ai deploy-full-local deploy-observability deploy-down
.PHONY: hybrid-up-recommendations cloud-check cloud-recommendations-check
.PHONY: wait wait-recommendations status
.PHONY: backend-run frontend-run frontend-build frontend-install backend-test backend-test-recommendations backend-lint backend-compile
.PHONY: recommendations-test recommendations-smoke recommendations-curl
.PHONY: logs-ragflow logs-searxng logs-tei logs-vllm logs-backend
.PHONY: stop-ragflow stop-searxng stop-tei stop-vllm docs-check doctor

help:
	@echo "Корневые команды ПрофИИта"
	@echo ""
	@echo "  Настройка:"
	@echo "    make init                         Подготовить env-файлы для всех локальных сервисов"
	@echo "    make init-core                    Подготовить env-файлы backend/frontend"
	@echo "    make init-recommendations         Подготовить env/config для RAGFlow, SearXNG, TEI"
	@echo "    make pull-recommendations         Скачать/подготовить артефакты RAGFlow, SearXNG, TEI"
	@echo "    make pull-ai-local                Скачать/подготовить vLLM + recommendation-сервисы"
	@echo ""
	@echo "  Локальный запуск:"
	@echo "    make local-up-core                Запустить локальную БД и применить миграции"
	@echo "    make local-up-recommendations     Запустить TEI, RAGFlow и SearXNG локально"
	@echo "    make local-up-ai                  Запустить vLLM + recommendation-сервисы локально"
	@echo "    make local-up                     Запустить ядро + recommendation-сервисы"
	@echo "    make local-down-recommendations   Остановить TEI, RAGFlow и SearXNG"
	@echo "    make local-down                   Остановить recommendation-сервисы и БД"
	@echo ""
	@echo "  Docker/деплой всего приложения:"
	@echo "    make compose-build                Собрать Docker images backend/frontend"
	@echo "    make compose-up-core              Запустить PostgreSQL из root docker-compose.yml"
	@echo "    make compose-up-app               Запустить PostgreSQL + backend + frontend в Docker"
	@echo "    make deploy-local-core            Полный Docker core: Postgres + backend + frontend"
	@echo "    make deploy-local-rag             Core app + локальные TEI/RAGFlow/SearXNG"
	@echo "    make deploy-local-ai              Core app + локальный vLLM + TEI/RAGFlow/SearXNG"
	@echo "    make deploy-hybrid-llm-local-rag  Cloud/external LLM + локальные RAG/search/embeddings"
	@echo "    make deploy-cloud-ai              Backend/frontend в Docker + внешние AI/RAG endpoints"
	@echo "    make deploy-full-local            vLLM + рекомендации + Graylog + app в Docker"
	@echo "    make deploy-down                  Остановить root compose и локальные AI/RAG сервисы"
	@echo ""
	@echo "  Гибридный/cloud запуск:"
	@echo "    make hybrid-up-recommendations    Запустить локальные RAG/search/embeddings с cloud/external LLM"
	@echo "    make cloud-check                  Проверить env для cloud/external endpoint"
	@echo "    make cloud-recommendations-check  Проверить env для RAGFlow/SearXNG/TEI endpoint"
	@echo ""
	@echo "  Тесты и проверка:"
	@echo "    make backend-test                 Запустить backend tests"
	@echo "    make backend-test-recommendations Запустить recommendation + AI chat tests"
	@echo "    make backend-lint                 Запустить backend ruff"
	@echo "    make recommendations-test         Запустить smoke tests RAGFlow/SearXNG/TEI"
	@echo "    make recommendations-curl         Показать API curl-примеры"
	@echo "    make doctor                       Показать сводку готовности деплоя"
	@echo ""
	@echo "  Логи и статус:"
	@echo "    make status                       Показать статус локальных сервисов"
	@echo "    make logs-ragflow | logs-searxng | logs-tei | logs-vllm"
	@echo ""
	@echo "  Процессы приложения:"
	@echo "    make backend-run                  Запустить FastAPI dev server"
	@echo "    make frontend-run                 Запустить Next.js dev server"
	@echo "    make frontend-build               Собрать frontend"

init: init-core init-recommendations init-observability init-voice

init-core:
	@test -f .env || cp backend/.env.example .env
	@test -f $(BACKEND_DIR)/.env || cp $(BACKEND_DIR)/.env.example $(BACKEND_DIR)/.env
	@test -f $(FRONTEND_DIR)/.env || { test ! -f $(FRONTEND_DIR)/.env.example || cp $(FRONTEND_DIR)/.env.example $(FRONTEND_DIR)/.env; }
	@echo "Env-файлы ядра готовы"

init-recommendations:
	$(MAKE) -C $(TEI_DIR) init
	$(MAKE) -C $(RAGFLOW_DIR) init
	$(MAKE) -C $(SEARXNG_DIR) init

init-observability:
	@test ! -d $(GRAYLOG_DIR) || $(MAKE) -C $(GRAYLOG_DIR) init-env

init-voice:
	@if [ -d "$(WHISPER_DIR)" ] && [ -f "$(WHISPER_DIR)/.env.example" ] && [ ! -f "$(WHISPER_DIR)/.env" ]; then \
		cp "$(WHISPER_DIR)/.env.example" "$(WHISPER_DIR)/.env"; \
		echo "whisper-server/.env готов"; \
	fi

pull: pull-recommendations

pull-recommendations:
	$(MAKE) -C $(TEI_DIR) pull
	$(MAKE) -C $(RAGFLOW_DIR) fetch
	$(MAKE) -C $(RAGFLOW_DIR) configure
	$(MAKE) -C $(RAGFLOW_DIR) pull
	$(MAKE) -C $(SEARXNG_DIR) pull

pull-ai-local:
	$(MAKE) -C $(VLLM_DIR) pull
	$(MAKE) pull-recommendations

local-up: local-up-core local-up-recommendations

local-up-core:
	$(MAKE) -C $(BACKEND_DIR) db-up
	$(MAKE) -C $(BACKEND_DIR) migrate

local-up-recommendations:
	$(MAKE) -C $(TEI_DIR) run
	$(MAKE) -C $(RAGFLOW_DIR) up
	$(MAKE) -C $(SEARXNG_DIR) run
	$(MAKE) wait-recommendations

local-up-ai:
	$(MAKE) -C $(VLLM_DIR) run
	$(MAKE) local-up-recommendations

hybrid-up-recommendations: local-up-recommendations
	@echo "Гибридный режим: локальные RAG/search/embeddings запущены. Настройте backend LLM_* env vars для cloud/external LLM."

local-down: local-down-recommendations
	-$(MAKE) -C $(BACKEND_DIR) db-stop

local-down-recommendations:
	-$(MAKE) -C $(SEARXNG_DIR) stop
	-$(MAKE) -C $(RAGFLOW_DIR) down
	-$(MAKE) -C $(TEI_DIR) stop

compose-build: init-core
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) --profile app build

compose-up-core: init-core
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) --profile core up -d postgres

compose-up-app: init-core
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) --profile app up -d --build postgres backend frontend

compose-down:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) --profile app --profile core down

compose-logs:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) logs -f

compose-ps:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) --profile app --profile core ps

deploy-local-core: init-core compose-up-app
	@echo "Core deployment ready: frontend http://localhost:$${FRONTEND_PORT:-3000}, backend http://localhost:$${BACKEND_PORT:-8001}/api/v1"

deploy-local-rag: init pull-recommendations local-up-recommendations compose-up-app
	@echo "Hybrid local RAG deployment ready. Убедитесь, что backend/.env содержит RECOMMENDATIONS_ENABLED=true, RAGFLOW_API_KEY и RAGFLOW_DATASET_ID."

deploy-local-ai: init pull-ai-local local-up-ai compose-up-app
	@echo "Fully local AI deployment ready. Убедитесь, что backend/.env указывает LLM_BASE_URL=http://host.docker.internal:8100/v1 для backend container."

deploy-hybrid-llm-local-rag: init-recommendations pull-recommendations local-up-recommendations compose-up-app
	@echo "Hybrid deployment ready: внешний/cloud LLM + локальные RAG/search/embeddings."

deploy-cloud-ai: init-core cloud-check cloud-recommendations-check compose-up-app
	@echo "Cloud AI deployment ready: backend/frontend в Docker, AI/RAG endpoints берутся из env."

deploy-observability:
	$(MAKE) -C $(GRAYLOG_DIR) up
	$(MAKE) -C $(GRAYLOG_DIR) configure

deploy-full-local: init pull-ai-local local-up-ai deploy-observability compose-up-app
	@echo "Full local deployment ready: app + vLLM + TEI + RAGFlow + SearXNG + Graylog."

deploy-down: compose-down local-down-recommendations
	-$(MAKE) -C $(VLLM_DIR) stop
	-$(MAKE) -C $(GRAYLOG_DIR) down

wait: wait-recommendations

wait-recommendations:
	$(MAKE) -C $(TEI_DIR) wait
	$(MAKE) -C $(RAGFLOW_DIR) wait
	$(MAKE) -C $(SEARXNG_DIR) wait

backend-run:
	$(MAKE) -C $(BACKEND_DIR) run

frontend-install:
	cd $(FRONTEND_DIR) && npm install

frontend-run:
	cd $(FRONTEND_DIR) && npm run dev

frontend-build:
	cd $(FRONTEND_DIR) && npm run build

backend-test:
	cd $(BACKEND_DIR) && $(BACKEND_PYTEST) tests/ -q

backend-test-recommendations:
	cd $(BACKEND_DIR) && $(BACKEND_PYTEST) tests/test_recommendations.py tests/test_ai_chat.py -q

backend-lint:
	cd $(BACKEND_DIR) && $(BACKEND_RUFF) check app tests scripts

backend-compile:
	cd $(BACKEND_DIR) && $(BACKEND_PYTHON) -m compileall -q app tests scripts

recommendations-test:
	$(MAKE) -C $(TEI_DIR) test
	$(MAKE) -C $(RAGFLOW_DIR) test
	$(MAKE) -C $(SEARXNG_DIR) test

recommendations-smoke: backend-test-recommendations recommendations-test

recommendations-curl:
	$(MAKE) -C $(TEI_DIR) curl-examples
	@echo ""
	$(MAKE) -C $(RAGFLOW_DIR) curl-examples
	@echo ""
	$(MAKE) -C $(SEARXNG_DIR) curl-examples

cloud-check:
	@./scripts/check_cloud_env.sh

cloud-recommendations-check:
	@./scripts/check_recommendation_env.sh

doctor:
	@./scripts/doctor.sh

docs-check:
	@echo "Доступная документация:"
	@echo "  README.md"
	@echo "  docs/deployment.md"
	@echo "  docs/architecture-uml.md"
	@echo "  docs/hackathon-readiness.md"
	@echo "  backend/docs/recommendations.md"
	@echo "  backend/docs/recommendation_examples.md"
	@echo "  backend/docs/ragflow_dataset_setup.md"
	@echo "  ragflow/README.md"
	@echo "  searxng/README.md"
	@echo "  tei/README.md"

status:
	@echo "Backend DB:"
	@docker ps -a --filter "name=findoctor-postgres" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || true
	@echo ""
	@echo "Recommendation services:"
	@$(MAKE) -C $(TEI_DIR) ps
	@$(MAKE) -C $(SEARXNG_DIR) ps
	@$(MAKE) -C $(RAGFLOW_DIR) ps || true

logs-ragflow:
	$(MAKE) -C $(RAGFLOW_DIR) logs

logs-searxng:
	$(MAKE) -C $(SEARXNG_DIR) logs

logs-tei:
	$(MAKE) -C $(TEI_DIR) logs

logs-vllm:
	$(MAKE) -C $(VLLM_DIR) logs

logs-backend:
	$(MAKE) -C $(BACKEND_DIR) db-logs

stop-ragflow:
	$(MAKE) -C $(RAGFLOW_DIR) down

stop-searxng:
	$(MAKE) -C $(SEARXNG_DIR) stop

stop-tei:
	$(MAKE) -C $(TEI_DIR) stop

stop-vllm:
	$(MAKE) -C $(VLLM_DIR) stop
