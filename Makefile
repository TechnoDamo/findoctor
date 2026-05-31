SHELL := /bin/bash
export PATH := /opt/local/bin:$(PATH)

ROOT_DIR := $(CURDIR)

BACKEND_DIR := backend
FRONTEND_DIR := frontend
DB_DIR := db
RAGFLOW_DIR := ragflow
SEARXNG_DIR := searxng
TEI_DIR := tei
VLLM_DIR := vLLM
GRAYLOG_DIR := graylog
WHISPER_DIR := whisper-server

DOCKER ?= $(shell command -v docker 2>/dev/null || { test -x /opt/local/bin/docker && echo /opt/local/bin/docker; } || echo docker)
DOCKER_COMPOSE ?= $(DOCKER) compose
COMPOSE_FILE ?= docker-compose.yml

ENTITY ?= core
DEPLOYMENT ?= local

BACKEND_PYTEST := $(if $(wildcard $(BACKEND_DIR)/.venv/bin/pytest),./.venv/bin/pytest,pytest)
BACKEND_RUFF := $(if $(wildcard $(BACKEND_DIR)/.venv/bin/ruff),./.venv/bin/ruff,ruff)
BACKEND_PYTHON := $(if $(wildcard $(BACKEND_DIR)/.venv/bin/python),./.venv/bin/python,python3)

.PHONY: help deploy-system stop-system status-system logs-system
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
	@echo "ПрофИИт — корневой deployment dispatcher"
	@echo ""
	@echo "Канонический интерфейс:"
	@echo "  make deploy-system ENTITY=<entity> DEPLOYMENT=<local|cloud|hybrid>"
	@echo "  make stop-system   ENTITY=<entity>"
	@echo "  make status-system ENTITY=<entity>"
	@echo "  make logs-system   ENTITY=<entity>"
	@echo ""
	@echo "Entities:"
	@echo "  core              PostgreSQL + backend + frontend"
	@echo "  system            core + recommendations"
	@echo "  full              core + recommendations + vllm + graylog"
	@echo "  postgres          PostgreSQL"
	@echo "  backend           FastAPI backend"
	@echo "  frontend          Next.js frontend"
	@echo "  recommendations   TEI + RAGFlow + SearXNG"
	@echo "  ragflow           RAGFlow"
	@echo "  searxng/search    SearXNG"
	@echo "  tei/embeddings    Text Embeddings Inference"
	@echo "  vllm/llm          local OpenAI-compatible LLM"
	@echo "  whisper/stt       local STT proxy"
	@echo "  graylog/observability Graylog stack"
	@echo ""
	@echo "Examples:"
	@echo "  make deploy-system ENTITY=postgres DEPLOYMENT=local"
	@echo "  make deploy-system ENTITY=backend DEPLOYMENT=local"
	@echo "  make deploy-system ENTITY=recommendations DEPLOYMENT=cloud"
	@echo "  make deploy-system ENTITY=core DEPLOYMENT=local"
	@echo "  make deploy-system ENTITY=ai DEPLOYMENT=hybrid"
	@echo ""
	@echo "Compatibility aliases still exist: make local-up-core, make deploy-local-core, make backend-test, make docs-check."

deploy-system:
	@case "$(ENTITY):$(DEPLOYMENT)" in \
		core:local) \
			$(MAKE) -C $(DB_DIR) deploy-local && \
			$(MAKE) -C $(BACKEND_DIR) deploy-local && \
			$(MAKE) -C $(FRONTEND_DIR) deploy-local ;; \
		core:cloud) \
			$(MAKE) -C $(DB_DIR) deploy-cloud && \
			$(MAKE) -C $(BACKEND_DIR) deploy-cloud && \
			$(MAKE) -C $(FRONTEND_DIR) deploy-cloud ;; \
		system:local) \
			$(MAKE) deploy-system ENTITY=core DEPLOYMENT=local && \
			$(MAKE) deploy-system ENTITY=recommendations DEPLOYMENT=local ;; \
		system:cloud) \
			$(MAKE) deploy-system ENTITY=core DEPLOYMENT=cloud && \
			$(MAKE) deploy-system ENTITY=recommendations DEPLOYMENT=cloud ;; \
		full:local) \
			$(MAKE) deploy-system ENTITY=system DEPLOYMENT=local && \
			$(MAKE) deploy-system ENTITY=vllm DEPLOYMENT=local && \
			$(MAKE) deploy-system ENTITY=graylog DEPLOYMENT=local ;; \
		postgres:local|db:local) $(MAKE) -C $(DB_DIR) deploy-local ;; \
		postgres:cloud|db:cloud) $(MAKE) -C $(DB_DIR) deploy-cloud ;; \
		backend:local) $(MAKE) -C $(BACKEND_DIR) deploy-local ;; \
		backend:cloud) $(MAKE) -C $(BACKEND_DIR) deploy-cloud ;; \
		frontend:local) $(MAKE) -C $(FRONTEND_DIR) deploy-local ;; \
		frontend:cloud) $(MAKE) -C $(FRONTEND_DIR) deploy-cloud ;; \
		recommendations:local|rag:local) \
			$(MAKE) -C $(TEI_DIR) deploy-local && \
			$(MAKE) -C $(SEARXNG_DIR) deploy-local && \
			$(MAKE) -C $(RAGFLOW_DIR) deploy-local ;; \
		recommendations:cloud|rag:cloud) $(MAKE) cloud-recommendations-check ;; \
		ai:local) \
			$(MAKE) deploy-system ENTITY=vllm DEPLOYMENT=local && \
			$(MAKE) deploy-system ENTITY=recommendations DEPLOYMENT=local ;; \
		ai:cloud) \
			$(MAKE) deploy-system ENTITY=core DEPLOYMENT=cloud && \
			$(MAKE) cloud-check && \
			$(MAKE) cloud-recommendations-check ;; \
		ai:hybrid) \
			$(MAKE) cloud-check && \
			$(MAKE) deploy-system ENTITY=recommendations DEPLOYMENT=local ;; \
		ragflow:local) $(MAKE) -C $(RAGFLOW_DIR) deploy-local ;; \
		ragflow:cloud) $(MAKE) -C $(RAGFLOW_DIR) deploy-cloud ;; \
		searxng:local|search:local) $(MAKE) -C $(SEARXNG_DIR) deploy-local ;; \
		searxng:cloud|search:cloud) $(MAKE) -C $(SEARXNG_DIR) deploy-cloud ;; \
		tei:local|embeddings:local) $(MAKE) -C $(TEI_DIR) deploy-local ;; \
		tei:cloud|embeddings:cloud) $(MAKE) -C $(TEI_DIR) deploy-cloud ;; \
		vllm:local|llm:local) $(MAKE) -C $(VLLM_DIR) deploy-local ;; \
		vllm:cloud|llm:cloud) $(MAKE) cloud-check ;; \
		whisper:local|stt:local) $(MAKE) -C $(WHISPER_DIR) deploy-local ;; \
		whisper:cloud|stt:cloud) $(MAKE) cloud-check ;; \
		graylog:local|observability:local) $(MAKE) -C $(GRAYLOG_DIR) deploy-local ;; \
		graylog:cloud|observability:cloud) $(MAKE) -C $(GRAYLOG_DIR) deploy-cloud ;; \
		full:cloud) \
			echo "full deployment не поддерживает cloud-режим."; \
			echo "Используйте system:cloud для core+recommendations или разверните компоненты отдельно."; \
			exit 1 ;; \
		*) \
			echo "Unknown deployment matrix: ENTITY=$(ENTITY), DEPLOYMENT=$(DEPLOYMENT)"; \
			echo "Run: make help"; \
			exit 1 ;; \
	esac

stop-system:
	@case "$(ENTITY)" in \
		core) $(MAKE) -C $(FRONTEND_DIR) stop; $(MAKE) -C $(BACKEND_DIR) stop; $(MAKE) -C $(DB_DIR) stop ;; \
		system) $(MAKE) stop-system ENTITY=core; $(MAKE) stop-system ENTITY=recommendations ;; \
		full) $(MAKE) stop-system ENTITY=system; $(MAKE) stop-system ENTITY=vllm; $(MAKE) stop-system ENTITY=graylog ;; \
		postgres|db) $(MAKE) -C $(DB_DIR) stop ;; \
		backend) $(MAKE) -C $(BACKEND_DIR) stop ;; \
		frontend) $(MAKE) -C $(FRONTEND_DIR) stop ;; \
		recommendations|rag) $(MAKE) -C $(RAGFLOW_DIR) stop; $(MAKE) -C $(SEARXNG_DIR) stop; $(MAKE) -C $(TEI_DIR) stop ;; \
		ragflow) $(MAKE) -C $(RAGFLOW_DIR) stop ;; \
		searxng|search) $(MAKE) -C $(SEARXNG_DIR) stop ;; \
		tei|embeddings) $(MAKE) -C $(TEI_DIR) stop ;; \
		vllm|llm) $(MAKE) -C $(VLLM_DIR) stop ;; \
		whisper|stt) $(MAKE) -C $(WHISPER_DIR) stop ;; \
		graylog|observability) $(MAKE) -C $(GRAYLOG_DIR) stop ;; \
		*) echo "Unknown entity: $(ENTITY)"; exit 1 ;; \
	esac

status-system:
	@case "$(ENTITY)" in \
		core) $(MAKE) -C $(DB_DIR) status; $(MAKE) -C $(BACKEND_DIR) status; $(MAKE) -C $(FRONTEND_DIR) status ;; \
		system) $(MAKE) status-system ENTITY=core; $(MAKE) status-system ENTITY=recommendations ;; \
		postgres|db) $(MAKE) -C $(DB_DIR) status ;; \
		backend) $(MAKE) -C $(BACKEND_DIR) status ;; \
		frontend) $(MAKE) -C $(FRONTEND_DIR) status ;; \
		recommendations|rag) $(MAKE) -C $(TEI_DIR) status; $(MAKE) -C $(SEARXNG_DIR) status; $(MAKE) -C $(RAGFLOW_DIR) status ;; \
		ragflow) $(MAKE) -C $(RAGFLOW_DIR) status ;; \
		searxng|search) $(MAKE) -C $(SEARXNG_DIR) status ;; \
		tei|embeddings) $(MAKE) -C $(TEI_DIR) status ;; \
		vllm|llm) $(MAKE) -C $(VLLM_DIR) status ;; \
		whisper|stt) $(MAKE) -C $(WHISPER_DIR) status ;; \
		graylog|observability) $(MAKE) -C $(GRAYLOG_DIR) status ;; \
		*) echo "Unknown entity: $(ENTITY)"; exit 1 ;; \
	esac

logs-system:
	@case "$(ENTITY)" in \
		postgres|db) $(MAKE) -C $(DB_DIR) logs ;; \
		backend) $(MAKE) -C $(BACKEND_DIR) logs ;; \
		frontend) $(MAKE) -C $(FRONTEND_DIR) logs ;; \
		ragflow) $(MAKE) -C $(RAGFLOW_DIR) logs ;; \
		searxng|search) $(MAKE) -C $(SEARXNG_DIR) logs ;; \
		tei|embeddings) $(MAKE) -C $(TEI_DIR) logs ;; \
		vllm|llm) $(MAKE) -C $(VLLM_DIR) logs ;; \
		whisper|stt) $(MAKE) -C $(WHISPER_DIR) logs ;; \
		graylog|observability) $(MAKE) -C $(GRAYLOG_DIR) logs ;; \
		*) echo "logs-system supports one concrete service entity, got ENTITY=$(ENTITY)"; exit 1 ;; \
	esac

# ----------------------------------------------------------------------
# Compatibility aliases
# ----------------------------------------------------------------------
init: init-core init-recommendations init-observability init-voice

init-core:
	$(MAKE) -C $(BACKEND_DIR) init-env
	$(MAKE) -C $(FRONTEND_DIR) init
	@echo "Env-файлы ядра готовы (backend/.env и frontend/.env)"

init-recommendations:
	$(MAKE) -C $(TEI_DIR) init
	$(MAKE) -C $(RAGFLOW_DIR) init
	$(MAKE) -C $(SEARXNG_DIR) init

init-observability:
	@test ! -d $(GRAYLOG_DIR) || $(MAKE) -C $(GRAYLOG_DIR) init

init-voice:
	@test ! -d $(WHISPER_DIR) || $(MAKE) -C $(WHISPER_DIR) init

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
	$(MAKE) deploy-system ENTITY=core DEPLOYMENT=local

local-up-recommendations:
	$(MAKE) deploy-system ENTITY=recommendations DEPLOYMENT=local

local-up-ai:
	$(MAKE) deploy-system ENTITY=ai DEPLOYMENT=local

hybrid-up-recommendations:
	$(MAKE) deploy-system ENTITY=ai DEPLOYMENT=hybrid

local-down: local-down-recommendations
	$(MAKE) stop-system ENTITY=core

local-down-recommendations:
	$(MAKE) stop-system ENTITY=recommendations

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

deploy-local-core:
	$(MAKE) deploy-system ENTITY=core DEPLOYMENT=local

deploy-local-rag:
	$(MAKE) deploy-system ENTITY=system DEPLOYMENT=local

deploy-local-ai:
	$(MAKE) deploy-system ENTITY=ai DEPLOYMENT=local

deploy-hybrid-llm-local-rag:
	$(MAKE) deploy-system ENTITY=ai DEPLOYMENT=hybrid

deploy-cloud-ai:
	$(MAKE) deploy-system ENTITY=ai DEPLOYMENT=cloud

deploy-observability:
	$(MAKE) deploy-system ENTITY=graylog DEPLOYMENT=local

deploy-full-local:
	$(MAKE) deploy-system ENTITY=full DEPLOYMENT=local

deploy-down:
	$(MAKE) stop-system ENTITY=full

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
	@echo "  backend/README.md"
	@echo "  backend/docs/recommendations.md"
	@echo "  backend/docs/recommendation_examples.md"
	@echo "  backend/docs/ragflow_dataset_setup.md"
	@echo "  ragflow/README.md"
	@echo "  searxng/README.md"
	@echo "  tei/README.md"

status:
	$(MAKE) status-system ENTITY=system

logs-ragflow:
	$(MAKE) logs-system ENTITY=ragflow

logs-searxng:
	$(MAKE) logs-system ENTITY=searxng

logs-tei:
	$(MAKE) logs-system ENTITY=tei

logs-vllm:
	$(MAKE) logs-system ENTITY=vllm

logs-backend:
	$(MAKE) logs-system ENTITY=backend

stop-ragflow:
	$(MAKE) stop-system ENTITY=ragflow

stop-searxng:
	$(MAKE) stop-system ENTITY=searxng

stop-tei:
	$(MAKE) stop-system ENTITY=tei

stop-vllm:
	$(MAKE) stop-system ENTITY=vllm
