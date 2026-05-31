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

postgres ?= local
ragflow  ?= local
searxng  ?= local
graylog  ?= local
tei      ?= none
vllm     ?= none
whisper  ?= none

BACKEND_PYTEST := $(if $(wildcard $(BACKEND_DIR)/.venv/bin/pytest),./.venv/bin/pytest,pytest)
BACKEND_RUFF := $(if $(wildcard $(BACKEND_DIR)/.venv/bin/ruff),./.venv/bin/ruff,ruff)
BACKEND_PYTHON := $(if $(wildcard $(BACKEND_DIR)/.venv/bin/python),./.venv/bin/python,python3)

.PHONY: help deploy-system stop-system status-system logs-system stop-all
.PHONY: init init-core init-recommendations init-observability init-voice
.PHONY: pull pull-recommendations pull-ai-local
.PHONY: compose-build compose-up-core compose-up-app compose-down compose-logs compose-ps
.PHONY: cloud-check cloud-recommendations-check
.PHONY: backend-run frontend-run frontend-build frontend-install backend-test backend-test-recommendations backend-lint backend-compile
.PHONY: recommendations-test recommendations-smoke recommendations-curl
.PHONY: docs-check doctor

# Presets
.PHONY: preset-core preset-hybrid preset-fully-local preset-cloud

help:
	@echo "ПрофИИт — корневой per-component deployment dispatcher"
	@echo ""
	@echo "  make deploy-system [component=local|cloud|none ...]"
	@echo "  make deploy-system core | hybrid | fully-local | cloud"
	@echo ""
	@echo "Компоненты и флаги:"
	@echo "  backend / frontend   всегда Docker (флаги не требуются)"
	@echo "  postgres=local|cloud  [default: local]"
	@echo "  ragflow=local|cloud|none  [default: local]"
	@echo "  searxng=local|cloud|none  [default: local]"
	@echo "  graylog=local|cloud|none  [default: local]"
	@echo "  tei=local|none       [default: none]"
	@echo "  vllm=local|none      [default: none]"
	@echo "  whisper=local|none   [default: none]"
	@echo ""
	@echo "Пресеты:"
	@echo "  make deploy-system core          postgres=local, инфра=none, AI=none"
	@echo "  make deploy-system hybrid        cloud LLM + local RAG/search"
	@echo "  make deploy-system fully-local   всё локально"
	@echo "  make deploy-system cloud         всё cloud (только валидация env)"
	@echo ""
	@echo "Остановка / статус / логи:"
	@echo "  make stop-system   COMPONENTS=\"postgres ragflow vllm\""
	@echo "  make stop-system   COMPONENTS=all"
	@echo "  make status-system COMPONENTS=\"backend ragflow\""
	@echo "  make logs-system   COMPONENT=backend"
	@echo ""
	@echo "Примеры:"
	@echo "  make deploy-system                                        # дефолт"
	@echo "  make deploy-system vllm=local whisper=local               # + AI локально"
	@echo "  make deploy-system ragflow=cloud searxng=cloud            # RAG/search облачно"
	@echo "  make deploy-system graylog=none                           # без Graylog"
	@echo "  make deploy-system core                                   # только backend+frontend+postgres"
	@echo ""

# ----------------------------------------------------------------------
# deploy-system
# ----------------------------------------------------------------------
deploy-system:
	@echo "=== postgres ($(postgres)) ==="
	@case "$(postgres)" in \
		local) $(MAKE) -C $(DB_DIR) deploy-local ;; \
		cloud) $(MAKE) -C $(DB_DIR) deploy-cloud ;; \
		*) echo "Unknown flag: postgres=$(postgres)"; exit 1 ;; \
	esac
	@echo ""
	@echo "=== Core: backend + frontend ==="
	$(MAKE) -C $(BACKEND_DIR) deploy-local
	$(MAKE) -C $(FRONTEND_DIR) deploy-local
	@echo ""
	@echo "=== ragflow ($(ragflow)) ==="
	@case "$(ragflow)" in \
		local) $(MAKE) -C $(RAGFLOW_DIR) deploy-local ;; \
		cloud) $(MAKE) -C $(RAGFLOW_DIR) deploy-cloud ;; \
		none) echo "skipped" ;; \
		*) echo "Unknown flag: ragflow=$(ragflow)"; exit 1 ;; \
	esac
	@echo ""
	@echo "=== searxng ($(searxng)) ==="
	@case "$(searxng)" in \
		local) $(MAKE) -C $(SEARXNG_DIR) deploy-local ;; \
		cloud) $(MAKE) -C $(SEARXNG_DIR) deploy-cloud ;; \
		none) echo "skipped" ;; \
		*) echo "Unknown flag: searxng=$(searxng)"; exit 1 ;; \
	esac
	@echo ""
	@echo "=== graylog ($(graylog)) ==="
	@case "$(graylog)" in \
		local) $(MAKE) -C $(GRAYLOG_DIR) deploy-local ;; \
		cloud) $(MAKE) -C $(GRAYLOG_DIR) deploy-cloud ;; \
		none) echo "skipped" ;; \
		*) echo "Unknown flag: graylog=$(graylog)"; exit 1 ;; \
	esac
	@echo ""
	@echo "=== tei / embeddings ($(tei)) ==="
	@case "$(tei)" in \
		local) $(MAKE) -C $(TEI_DIR) deploy-local ;; \
		none) echo "skipped" ;; \
		*) echo "Unknown flag: tei=$(tei) (valid: local, none)"; exit 1 ;; \
	esac
	@echo ""
	@echo "=== vllm / LLM ($(vllm)) ==="
	@case "$(vllm)" in \
		local) $(MAKE) -C $(VLLM_DIR) deploy-local ;; \
		none) echo "skipped" ;; \
		*) echo "Unknown flag: vllm=$(vllm) (valid: local, none)"; exit 1 ;; \
	esac
	@echo ""
	@echo "=== whisper / STT ($(whisper)) ==="
	@case "$(whisper)" in \
		local) $(MAKE) -C $(WHISPER_DIR) deploy-local ;; \
		none) echo "skipped" ;; \
		*) echo "Unknown flag: whisper=$(whisper) (valid: local, none)"; exit 1 ;; \
	esac

# ----------------------------------------------------------------------
# Presets
# ----------------------------------------------------------------------
preset-core:
	$(MAKE) deploy-system postgres=local ragflow=none searxng=none graylog=none tei=none vllm=none whisper=none

preset-hybrid:
	$(MAKE) deploy-system postgres=local ragflow=local searxng=local graylog=local tei=local vllm=none whisper=none

preset-fully-local:
	$(MAKE) deploy-system postgres=local ragflow=local searxng=local graylog=local tei=local vllm=local whisper=local

preset-cloud:
	$(MAKE) deploy-system postgres=cloud ragflow=cloud searxng=cloud graylog=cloud tei=none vllm=none whisper=none
	@echo ""
	$(MAKE) cloud-check
	$(MAKE) cloud-recommendations-check

# ----------------------------------------------------------------------
# stop-system / status-system / logs-system
# ----------------------------------------------------------------------
stop-system:
	@if [ -z "$(COMPONENTS)" ]; then \
		echo "Usage: make stop-system COMPONENTS=\"postgres ragflow ...\" (or COMPONENTS=all)"; \
		exit 1; \
	fi
	@for comp in $(COMPONENTS); do \
		case "$$comp" in \
			postgres) $(MAKE) -C $(DB_DIR) stop ;; \
			backend)  $(MAKE) -C $(BACKEND_DIR) stop ;; \
			frontend) $(MAKE) -C $(FRONTEND_DIR) stop ;; \
			ragflow)  $(MAKE) -C $(RAGFLOW_DIR) stop ;; \
			searxng)  $(MAKE) -C $(SEARXNG_DIR) stop ;; \
			tei)      $(MAKE) -C $(TEI_DIR) stop ;; \
			vllm)     $(MAKE) -C $(VLLM_DIR) stop ;; \
			whisper)  $(MAKE) -C $(WHISPER_DIR) stop ;; \
			graylog)  $(MAKE) -C $(GRAYLOG_DIR) stop ;; \
			all)      $(MAKE) stop-system COMPONENTS="postgres backend frontend ragflow searxng tei vllm whisper graylog" ;; \
			*) echo "Unknown component: $$comp"; exit 1 ;; \
		esac; \
	done

stop-all:
	$(MAKE) stop-system COMPONENTS=all

status-system:
	@if [ -z "$(COMPONENTS)" ]; then \
		echo "Usage: make status-system COMPONENTS=\"postgres backend ...\" (or COMPONENTS=all)"; \
		exit 1; \
	fi
	@for comp in $(COMPONENTS); do \
		case "$$comp" in \
			postgres) $(MAKE) -C $(DB_DIR) status ;; \
			backend)  $(MAKE) -C $(BACKEND_DIR) status ;; \
			frontend) $(MAKE) -C $(FRONTEND_DIR) status ;; \
			ragflow)  $(MAKE) -C $(RAGFLOW_DIR) status ;; \
			searxng)  $(MAKE) -C $(SEARXNG_DIR) status ;; \
			tei)      $(MAKE) -C $(TEI_DIR) status ;; \
			vllm)     $(MAKE) -C $(VLLM_DIR) status ;; \
			whisper)  $(MAKE) -C $(WHISPER_DIR) status ;; \
			graylog)  $(MAKE) -C $(GRAYLOG_DIR) status ;; \
			all)      $(MAKE) status-system COMPONENTS="postgres backend frontend ragflow searxng tei vllm whisper graylog" ;; \
			*) echo "Unknown component: $$comp"; exit 1 ;; \
		esac; \
	done

logs-system:
	@if [ -z "$(COMPONENT)" ]; then \
		echo "Usage: make logs-system COMPONENT=backend"; \
		exit 1; \
	fi
	@case "$(COMPONENT)" in \
		postgres) $(MAKE) -C $(DB_DIR) logs ;; \
		backend)  $(MAKE) -C $(BACKEND_DIR) logs ;; \
		frontend) $(MAKE) -C $(FRONTEND_DIR) logs ;; \
		ragflow)  $(MAKE) -C $(RAGFLOW_DIR) logs ;; \
		searxng)  $(MAKE) -C $(SEARXNG_DIR) logs ;; \
		tei)      $(MAKE) -C $(TEI_DIR) logs ;; \
		vllm)     $(MAKE) -C $(VLLM_DIR) logs ;; \
		whisper)  $(MAKE) -C $(WHISPER_DIR) logs ;; \
		graylog)  $(MAKE) -C $(GRAYLOG_DIR) logs ;; \
		*) echo "Unknown component: $(COMPONENT)"; exit 1 ;; \
	esac

# ----------------------------------------------------------------------
# Init
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

# ----------------------------------------------------------------------
# Pull / wait
# ----------------------------------------------------------------------
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

# ----------------------------------------------------------------------
# Compatibility aliases
# ----------------------------------------------------------------------
deploy-local-core:
	$(MAKE) deploy-system postgres=local ragflow=none searxng=none graylog=none tei=none vllm=none whisper=none

deploy-local-rag:
	$(MAKE) deploy-system

deploy-local-ai:
	$(MAKE) deploy-system vllm=local tei=local

deploy-hybrid-llm-local-rag:
	$(MAKE) deploy-system tei=local

deploy-cloud-ai:
	$(MAKE) deploy-system postgres=cloud ragflow=cloud searxng=cloud graylog=cloud tei=none vllm=none whisper=none
	@echo ""
	$(MAKE) cloud-check
	$(MAKE) cloud-recommendations-check

deploy-full-local:
	$(MAKE) deploy-system vllm=local tei=local whisper=local

deploy-observability:
	$(MAKE) -C $(GRAYLOG_DIR) deploy-local

deploy-down:
	$(MAKE) stop-system COMPONENTS=all

# Old names kept for muscle memory
local-up-core:     deploy-local-core
local-up-recommendations: deploy-local-rag
local-up-ai:       deploy-local-ai
local-up:          deploy-local-rag
hybrid-up-recommendations: deploy-hybrid-llm-local-rag
local-down:        deploy-down
local-down-recommendations:
	$(MAKE) stop-system COMPONENTS="ragflow searxng tei"
status:
	$(MAKE) status-system COMPONENTS="postgres backend frontend ragflow searxng tei"

# ----------------------------------------------------------------------
# Docker compose helpers
# ----------------------------------------------------------------------
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

# ----------------------------------------------------------------------
# Dev / test / checks
# ----------------------------------------------------------------------
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

# ----------------------------------------------------------------------
# Component-specific logs/stop (muscle memory shortcuts)
# ----------------------------------------------------------------------
logs-ragflow:
	$(MAKE) logs-system COMPONENT=ragflow

logs-searxng:
	$(MAKE) logs-system COMPONENT=searxng

logs-tei:
	$(MAKE) logs-system COMPONENT=tei

logs-vllm:
	$(MAKE) logs-system COMPONENT=vllm

logs-backend:
	$(MAKE) logs-system COMPONENT=backend

stop-ragflow:
	$(MAKE) stop-system COMPONENTS=ragflow

stop-searxng:
	$(MAKE) stop-system COMPONENTS=searxng

stop-tei:
	$(MAKE) stop-system COMPONENTS=tei

stop-vllm:
	$(MAKE) stop-system COMPONENTS=vllm
