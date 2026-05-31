SHELL := /bin/bash
export PATH := /opt/local/bin:$(PATH)

ENV_FILE := .env

ifneq (,$(wildcard $(ENV_FILE)))
include $(ENV_FILE)
export
endif

VLLM_MODEL                ?= Qwen/Qwen2.5-1.5B-Instruct
VLLM_REVISION             ?=
VLLM_TOKENIZER_MODE       ?= auto
VLLM_HOST                 ?= 0.0.0.0
VLLM_PORT                 ?= 8100
VLLM_CONTAINER_NAME       ?= vllm-findoctor
VLLM_ACCELERATION         ?=
VLLM_TENSOR_PARALLEL      ?= 1
VLLM_GPU_MEMORY_UTILIZATION ?= 0.90
VLLM_MAX_MODEL_LEN        ?=
VLLM_MAX_NUM_SEQS         ?= 256
VLLM_MAX_NUM_BATCHED_TOKENS ?=
VLLM_CPU_THREADS          ?=
VLLM_MODELS_DIR           ?= ./models
VLLM_HF_HOME              ?= /root/.cache/huggingface
VLLM_LOG_LEVEL            ?= info
VLLM_IMAGE                ?=
VLLM_PLATFORM             ?=
VLLM_BENCH_ITERATIONS     ?= 5
VLLM_BENCH_CONCURRENCY    ?= 2

UNAME_S := $(shell uname -s)
UNAME_M := $(shell uname -m)

# --- hardware / image selection ---
ifeq ($(VLLM_ACCELERATION),cuda)
  DETECTED_ACCEL := cuda
  VLLM_IMAGE := vllm/vllm-openai:latest
  GPU_DOCKER_FLAGS := --gpus all
else ifeq ($(VLLM_ACCELERATION),rocm)
  DETECTED_ACCEL := rocm
  VLLM_IMAGE := rocm/vllm:latest
  GPU_DOCKER_FLAGS := --device /dev/kfd --device /dev/dri --group-add video
else ifeq ($(VLLM_ACCELERATION),cpu)
  DETECTED_ACCEL := cpu
  VLLM_IMAGE := vllm/vllm-openai:latest-cpu
  GPU_DOCKER_FLAGS :=
else
  ifeq ($(UNAME_S),Linux)
    HAS_NVIDIA := $(shell command -v nvidia-smi 2>/dev/null)
    ifneq (,$(HAS_NVIDIA))
      DETECTED_ACCEL := cuda
      VLLM_IMAGE := vllm/vllm-openai:latest
      GPU_DOCKER_FLAGS := --gpus all
    else
      HAS_ROCM := $(shell command -v rocminfo 2>/dev/null)
      ifneq (,$(HAS_ROCM))
        DETECTED_ACCEL := rocm
        VLLM_IMAGE := rocm/vllm:latest
        GPU_DOCKER_FLAGS := --device /dev/kfd --device /dev/dri --group-add video
      else
        DETECTED_ACCEL := cpu
        VLLM_IMAGE := vllm/vllm-openai:latest-cpu
        GPU_DOCKER_FLAGS :=
      endif
    endif
  else
    DETECTED_ACCEL := cpu
    VLLM_IMAGE := vllm/vllm-openai:latest-cpu
    GPU_DOCKER_FLAGS :=
  endif
endif

VLLM_MODELS_DIR_ABS := $(abspath $(VLLM_MODELS_DIR))
VLLM_URL := http://$(VLLM_HOST):$(VLLM_PORT)

VLLM_ARGS := --model "$(VLLM_MODEL)" \
	--host "$(VLLM_HOST)" \
	--port $(VLLM_PORT) \
	--max-num-seqs $(VLLM_MAX_NUM_SEQS) \
	--gpu-memory-utilization $(VLLM_GPU_MEMORY_UTILIZATION) \
	--tokenizer-mode $(VLLM_TOKENIZER_MODE) \
	$(if $(VLLM_REVISION),--revision "$(VLLM_REVISION)",) \
	$(if $(VLLM_MAX_MODEL_LEN),--max-model-len $(VLLM_MAX_MODEL_LEN),) \
	$(if $(VLLM_MAX_NUM_BATCHED_TOKENS),--max-num-batched-tokens $(VLLM_MAX_NUM_BATCHED_TOKENS),) \
	--trust-remote-code

DOCKER_RUN_BASE := docker run -d \
	--name "$(VLLM_CONTAINER_NAME)" \
	-p $(VLLM_PORT):$(VLLM_PORT) \
	-v "$(VLLM_MODELS_DIR_ABS):$(VLLM_HF_HOME)" \
	-e HF_HOME=$(VLLM_HF_HOME) \
	-e VLLM_LOGGING_LEVEL=$(VLLM_LOG_LEVEL) \
	-e VLLM_NO_USAGE_STATS=1 \
	$(if $(VLLM_PLATFORM),--platform $(VLLM_PLATFORM),) \
	$(GPU_DOCKER_FLAGS) \
	$(VLLM_IMAGE)

RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
CYAN := \033[0;36m
MAGENTA := \033[0;35m
BOLD := \033[1m
NC := \033[0m

.PHONY: help init deploy-local deploy-cloud pull download-model run stop restart logs shell status info test bench clean clean-all

help:
	@echo "vLLM — локальный OpenAI-совместимый LLM-сервер"
	@echo ""
	@echo "  make init          Создать .env из .env.example"
	@echo "  make deploy-local  Полный локальный запуск: init, pull, run"
	@echo "  make deploy-cloud  Проверить external LLM endpoint config"
	@echo "  make pull          Скачать Docker-образ"
	@echo "  make download-model  Скачать модель в кэш без запуска сервера"
	@echo "  make run           Запустить vLLM-сервер на $(VLLM_HOST):$(VLLM_PORT)"
	@echo "  make stop          Остановить сервер"
	@echo "  make restart       Перезапустить сервер"
	@echo "  make logs          Логи контейнера (follow)"
	@echo "  make shell         Зайти в контейнер"
	@echo "  make info          Показать железо и конфигурацию"
	@echo "  make test          Запустить тесты API + бенчмарк производительности"
	@echo "  make bench         Только бенчмарк (сервер должен быть запущен)"
	@echo "  make clean         Удалить контейнер"
	@echo "  make clean-all     Удалить контейнер и кэш моделей"
	@echo ""
	@echo "Быстрый старт:"
	@echo "  make init && make pull && make run"

init:
	@test -f .env || cp .env.example .env
	@echo "vLLM/.env готов — отредактируйте модель и порт при необходимости"

deploy-local: init pull run

deploy-cloud:
	@test -n "$(LLM_BASE_URL)" || { echo "LLM_BASE_URL не задан"; exit 1; }
	@test -n "$(LLM_MODEL)" || { echo "LLM_MODEL не задан"; exit 1; }
	@if echo "$(LLM_BASE_URL)" | grep -Eq 'localhost|127\.0\.0\.1|host\.docker\.internal'; then \
		echo "LLM_BASE_URL выглядит локальным, а DEPLOYMENT=cloud ожидает external LLM endpoint."; \
		exit 1; \
	fi
	@echo "Cloud LLM config OK: $(LLM_BASE_URL), model=$(LLM_MODEL)"

pull:
	@echo "=== Скачивание Docker-образа: $(VLLM_IMAGE) ==="
	docker pull $(VLLM_IMAGE)
	@mkdir -p "$(VLLM_MODELS_DIR_ABS)"
	@echo "Готово. Модель скачается автоматически при первом запуске."

download-model:
	@echo "=== Скачивание модели $(VLLM_MODEL) в кэш ==="
	@mkdir -p "$(VLLM_MODELS_DIR_ABS)"
	docker run --rm \
		-v "$(VLLM_MODELS_DIR_ABS):$(VLLM_HF_HOME)" \
		-e HF_HOME=$(VLLM_HF_HOME) \
		$(if $(VLLM_PLATFORM),--platform $(VLLM_PLATFORM),) \
		$(VLLM_IMAGE) \
		python3 -c "from huggingface_hub import snapshot_download; print(snapshot_download('$(VLLM_MODEL)'$(if $(VLLM_REVISION), revision='$(VLLM_REVISION)'))))"
	@echo "Модель загружена в $(VLLM_MODELS_DIR_ABS)"

run:
	@if docker ps -a --format '{{.Names}}' | grep -qx '$(VLLM_CONTAINER_NAME)'; then \
		echo "Контейнер $(VLLM_CONTAINER_NAME) уже существует."; \
		echo "Для перезапуска: make restart"; \
		echo "Для удаления:    make clean"; \
		exit 1; \
	fi
	@mkdir -p "$(VLLM_MODELS_DIR_ABS)"
	@echo "=== Запуск vLLM-сервера ==="
	@echo "Модель:     $(VLLM_MODEL)"
	@echo "Ускорение:  $(DETECTED_ACCEL)"
	@echo "Образ:      $(VLLM_IMAGE)"
	@echo "URL:        $(VLLM_URL)/v1"
	@echo "Кэш:        $(VLLM_MODELS_DIR_ABS)"
	@echo ""
	$(DOCKER_RUN_BASE) $(VLLM_ARGS)
	@echo ""
	@echo "Контейнер запущен. Ожидание загрузки модели..."
	@echo "Следите за логами: make logs"
	@echo "Проверить готовность: curl -s $(VLLM_URL)/health"

stop:
	@echo "=== Остановка vLLM ==="
	docker stop "$(VLLM_CONTAINER_NAME)" 2>/dev/null || echo "Контейнер не запущен"
	docker rm "$(VLLM_CONTAINER_NAME)" 2>/dev/null || true

restart:
	@echo "=== Перезапуск vLLM ==="
	-docker stop "$(VLLM_CONTAINER_NAME)" 2>/dev/null
	-docker rm "$(VLLM_CONTAINER_NAME)" 2>/dev/null
	$(MAKE) run

logs:
	@docker logs -f "$(VLLM_CONTAINER_NAME)"

shell:
	@docker exec -it "$(VLLM_CONTAINER_NAME)" bash

status:
	@docker ps -a --filter "name=$(VLLM_CONTAINER_NAME)" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

info:
	@echo "=== Система ==="
	@echo "OS:            $(UNAME_S)"
	@echo "Архитектура:   $(UNAME_M)"
	@echo ""
	@echo "=== Аппаратное ускорение ==="
	@echo "Бэкенд:        $(DETECTED_ACCEL)"
	@echo "Docker-образ:  $(VLLM_IMAGE)"
	@echo "GPU-флаги:     $(if $(GPU_DOCKER_FLAGS),$(GPU_DOCKER_FLAGS),нет (CPU-режим))"
	@echo ""
	@echo "=== Модель ==="
	@echo "Модель:        $(VLLM_MODEL)"
	@echo "Ревизия:       $(if $(VLLM_REVISION),$(VLLM_REVISION),основная)"
	@echo "Кэш моделей:   $(VLLM_MODELS_DIR_ABS)"
	@if [ -d "$(VLLM_MODELS_DIR_ABS)" ]; then \
		CACHE_SIZE=$$(du -sh "$(VLLM_MODELS_DIR_ABS)" 2>/dev/null | cut -f1); \
		echo "Размер кэша:   $$CACHE_SIZE"; \
	else \
		echo "Размер кэша:   (директория не создана)"; \
	fi
	@echo ""
	@echo "=== Сервер ==="
	@echo "URL:           $(VLLM_URL)/v1"
	@echo "Порт:          $(VLLM_PORT)"
	@echo "Контейнер:     $(VLLM_CONTAINER_NAME)"
	@echo "Max seqs:      $(VLLM_MAX_NUM_SEQS)"
	@echo "GPU mem:       $(VLLM_GPU_MEMORY_UTILIZATION)"
	@echo ""
	@echo "=== Контейнер ==="
	@docker ps -a --filter "name=$(VLLM_CONTAINER_NAME)" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "  (не создан)"
	@echo ""
	@echo "=== Эндпоинты OpenAI ==="
	@echo "  Список моделей:  GET  $(VLLM_URL)/v1/models"
	@echo "  Chat:            POST $(VLLM_URL)/v1/chat/completions"
	@echo "  Health:          GET  $(VLLM_URL)/health"
	@echo ""
	@echo "Интеграция с backend:"
	@echo "  LLM_BASE_URL=$(VLLM_URL)/v1"
	@echo "  LLM_API_KEY=not-needed"
	@echo "  LLM_MODEL=$(VLLM_MODEL)"

# --- test / benchmark ---
TEST_PORT := 18100
TEST_URL := http://127.0.0.1:$(TEST_PORT)
TEST_BENCH_SCRIPT := /tmp/vllm-bench-$$$$.py

test:
	@FAILED=0; TOTAL=0; \
	\
	echo -e "$(BOLD)=== vLLM Test Suite ===$(NC)"; \
	echo ""; \
	\
	USE_EXISTING=0; \
	if curl -s --max-time 2 "$(VLLM_URL)/health" > /dev/null 2>&1; then \
		echo "[setup] Сервер уже запущен на $(VLLM_URL), использую его"; \
		TEST_URL="$(VLLM_URL)"; \
		USE_EXISTING=1; \
	else \
		echo "[setup] Запускаю временный тестовый сервер на порту $(TEST_PORT)..."; \
		lsof -ti:$(TEST_PORT) 2>/dev/null | xargs kill -9 2>/dev/null || true; \
		mkdir -p "$(VLLM_MODELS_DIR_ABS)"; \
		docker run -d \
			--name "vllm-test-$$$$" \
			-p $(TEST_PORT):$(TEST_PORT) \
			-v "$(VLLM_MODELS_DIR_ABS):$(VLLM_HF_HOME)" \
			-e HF_HOME=$(VLLM_HF_HOME) \
			-e VLLM_LOGGING_LEVEL=error \
			-e VLLM_NO_USAGE_STATS=1 \
			$(if $(VLLM_PLATFORM),--platform $(VLLM_PLATFORM),) \
			$(GPU_DOCKER_FLAGS) \
			$(VLLM_IMAGE) \
			--model "$(VLLM_MODEL)" \
			--host 0.0.0.0 \
			--port $(TEST_PORT) \
			--max-num-seqs 8 \
			--gpu-memory-utilization 0.50 \
			$(if $(VLLM_REVISION),--revision "$(VLLM_REVISION)",) \
			$(if $(VLLM_MAX_MODEL_LEN),--max-model-len $(VLLM_MAX_MODEL_LEN),--max-model-len 4096) \
			--trust-remote-code \
			> /tmp/vllm-test-server.log 2>&1; \
		\
		echo -n "[setup] Ожидание загрузки модели"; \
		for i in {1..180}; do \
			if curl -s --max-time 2 "$(TEST_URL)/health" > /dev/null 2>&1; then \
				echo " готово ($${i}с)"; break; \
			fi; \
			sleep 2; echo -n .; \
		done; \
		echo ""; \
		if ! curl -s --max-time 2 "$(TEST_URL)/health" > /dev/null 2>&1; then \
			echo -e "$(RED)Сервер не запустился за отведённое время$(NC)"; \
			docker logs "vllm-test-$$$$" 2>/dev/null | tail -20; \
			docker rm -f "vllm-test-$$$$" 2>/dev/null || true; \
			exit 1; \
		fi; \
	fi; \
	\
	echo ""; \
	echo -e "$(BOLD)=== Тесты ===$(NC)"; \
	echo ""; \
	\
	TOTAL=$$((TOTAL+1)); \
	echo "1. Health-чек"; \
	STATUS=$$(curl -s -o /tmp/vllm-test-health.txt -w '%{http_code}' --max-time 10 "$(TEST_URL)/health"); \
	if [ "$$STATUS" = "200" ]; then \
		echo -e "  $(GREEN)PASS$(NC)  $$STATUS  сервер жив"; \
	else \
		echo -e "  $(RED)FAIL$(NC)  $$STATUS"; \
		FAILED=$$((FAILED+1)); \
	fi; \
	\
	TOTAL=$$((TOTAL+1)); \
	echo "2. GET /v1/models (список моделей)"; \
	curl -s -o /tmp/vllm-test-models.json --max-time 10 "$(TEST_URL)/v1/models"; \
	STATUS=$$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$(TEST_URL)/v1/models"); \
	if [ "$$STATUS" = "200" ]; then \
		MODEL_COUNT=$$(python3 -c "import json; d=json.load(open('/tmp/vllm-test-models.json')); print(len(d.get('data',[])))" 2>/dev/null); \
		if [ "$$MODEL_COUNT" -gt 0 ]; then \
			MODEL_ID=$$(python3 -c "import json; d=json.load(open('/tmp/vllm-test-models.json')); print(d['data'][0]['id'])" 2>/dev/null); \
			echo -e "  $(GREEN)PASS$(NC)  $$STATUS  $$MODEL_COUNT модель(ей), id=$$MODEL_ID"; \
		else \
			echo -e "  $(YELLOW)WARN$(NC)  $$STATUS  пустой список моделей"; \
		fi; \
	else \
		echo -e "  $(RED)FAIL$(NC)  $$STATUS"; \
		FAILED=$$((FAILED+1)); \
	fi; \
	\
	TOTAL=$$((TOTAL+1)); \
	echo "3. Chat non-streaming (простой запрос)"; \
	STATUS=$$(curl -s -o /tmp/vllm-test-chat.json -w '%{http_code}' --max-time 120 \
		-X POST "$(TEST_URL)/v1/chat/completions" \
		-H 'Content-Type: application/json' \
		-d '{"model":"$(VLLM_MODEL)","messages":[{"role":"user","content":"Скажи ровно два слова: Привет мир"}],"temperature":0,"max_tokens":50}'); \
	if [ "$$STATUS" = "200" ]; then \
		HAS_CONTENT=$$(python3 -c "import json; d=json.load(open('/tmp/vllm-test-chat.json')); print('yes' if d['choices'][0]['message'].get('content') else 'no')" 2>/dev/null); \
		if [ "$$HAS_CONTENT" = "yes" ]; then \
			CONTENT=$$(python3 -c "import json; d=json.load(open('/tmp/vllm-test-chat.json')); print(d['choices'][0]['message']['content'][:80])" 2>/dev/null); \
			TOKENS=$$(python3 -c "import json; d=json.load(open('/tmp/vllm-test-chat.json')); u=d.get('usage',{}); print(f\"in={u.get('prompt_tokens',0)} out={u.get('completion_tokens',0)}\")" 2>/dev/null); \
			echo -e "  $(GREEN)PASS$(NC)  $$STATUS  $$TOKENS  text=\"$$CONTENT\""; \
		else \
			echo -e "  $(RED)FAIL$(NC)  $$STATUS  пустой content"; \
			FAILED=$$((FAILED+1)); \
		fi; \
	else \
		echo -e "  $(RED)FAIL$(NC)  $$STATUS"; \
		cat /tmp/vllm-test-chat.json 2>/dev/null | head -5; \
		FAILED=$$((FAILED+1)); \
	fi; \
	\
	TOTAL=$$((TOTAL+1)); \
	echo "4. Chat streaming (SSE)"; \
	STATUS=$$(curl -s -o /tmp/vllm-test-stream.txt -w '%{http_code}' --max-time 120 \
		-X POST "$(TEST_URL)/v1/chat/completions" \
		-H 'Content-Type: application/json' \
		-d '{"model":"$(VLLM_MODEL)","messages":[{"role":"user","content":"Одно слово: да"}],"temperature":0,"max_tokens":20,"stream":true}'); \
	if [ "$$STATUS" = "200" ]; then \
		LINES=$$(wc -l < /tmp/vllm-test-stream.txt | tr -d ' '); \
		HAS_DATA=$$(grep -c '"delta"' /tmp/vllm-test-stream.txt 2>/dev/null || echo 0); \
		if [ "$$LINES" -gt 0 ] && [ "$$HAS_DATA" -gt 0 ]; then \
			NON_EMPTY=$$(python3 -c 'import json; text=""; exec("for ln in open(\"/tmp/vllm-test-stream.txt\"):\n ln=ln.strip()\n if ln.startswith(\"data: \") and ln[6:]!=\"[DONE]\":\n  try:\n   d=json.loads(ln[6:])\n   text+=d[\"choices\"][0].get(\"delta\",{}).get(\"content\",\"\")\n  except: pass\nprint(text[:60])")' 2>/dev/null); \
			echo -e "  $(GREEN)PASS$(NC)  $$STATUS  $$LINES строк, $$HAS_DATA data-фреймов, текст=\"$$NON_EMPTY\""; \
		else \
			echo -e "  $(YELLOW)WARN$(NC)  $$STATUS  $$LINES строк, data-фреймов=$$HAS_DATA"; \
		fi; \
	else \
		echo -e "  $(RED)FAIL$(NC)  $$STATUS"; \
		FAILED=$$((FAILED+1)); \
	fi; \
	\
	TOTAL=$$((TOTAL+1)); \
	echo "5. Temperature=0 (детерминированность)"; \
	curl -s -o /tmp/vllm-test-det1.json --max-time 60 \
		-X POST "$(TEST_URL)/v1/chat/completions" \
		-H 'Content-Type: application/json' \
		-d '{"model":"$(VLLM_MODEL)","messages":[{"role":"user","content":"Ответь числом от 1 до 5, только число"}],"temperature":0,"max_tokens":5}'; \
	curl -s -o /tmp/vllm-test-det2.json --max-time 60 \
		-X POST "$(TEST_URL)/v1/chat/completions" \
		-H 'Content-Type: application/json' \
		-d '{"model":"$(VLLM_MODEL)","messages":[{"role":"user","content":"Ответь числом от 1 до 5, только число"}],"temperature":0,"max_tokens":5}'; \
	T1=$$(python3 -c "import json; d=json.load(open('/tmp/vllm-test-det1.json')); print(d['choices'][0]['message'].get('content','').strip()[:10])" 2>/dev/null); \
	T2=$$(python3 -c "import json; d=json.load(open('/tmp/vllm-test-det2.json')); print(d['choices'][0]['message'].get('content','').strip()[:10])" 2>/dev/null); \
	if [ "$$T1" = "$$T2" ] && [ -n "$$T1" ]; then \
		echo -e "  $(GREEN)PASS$(NC)  детерминированный ответ: \"$$T1\""; \
	else \
		echo -e "  $(YELLOW)WARN$(NC)  ответы различаются (\"$$T1\" vs \"$$T2\" — flash-attention?)"; \
	fi; \
	\
	TOTAL=$$((TOTAL+1)); \
	echo "6. System prompt"; \
	curl -s -o /tmp/vllm-test-system.json --max-time 60 \
		-X POST "$(TEST_URL)/v1/chat/completions" \
		-H 'Content-Type: application/json' \
		-d '{"model":"$(VLLM_MODEL)","messages":[{"role":"system","content":"Ты — робот. Всегда начинай ответ словом БИП."},{"role":"user","content":"Поздоровайся"}],"temperature":0,"max_tokens":30}'; \
	SYS_TEXT=$$(python3 -c "import json; d=json.load(open('/tmp/vllm-test-system.json')); print(d['choices'][0]['message'].get('content','')[:60])" 2>/dev/null); \
	if echo "$$SYS_TEXT" | grep -qi "бип\|БИП\|bip\|BIP"; then \
		echo -e "  $(GREEN)PASS$(NC)  system prompt учтён: \"$$SYS_TEXT\""; \
	else \
		echo -e "  $(YELLOW)WARN$(NC)  system prompt не учтён: \"$$SYS_TEXT\""; \
	fi; \
	\
	TOTAL=$$((TOTAL+1)); \
	echo "7. Русский язык"; \
	curl -s -o /tmp/vllm-test-ru.json --max-time 60 \
		-X POST "$(TEST_URL)/v1/chat/completions" \
		-H 'Content-Type: application/json' \
		-d '{"model":"$(VLLM_MODEL)","messages":[{"role":"user","content":"Ответь на русском языке: как дела?"}],"temperature":0.3,"max_tokens":50}'; \
	RU_TEXT=$$(python3 -c "import json; d=json.load(open('/tmp/vllm-test-ru.json')); print(d['choices'][0]['message'].get('content','')[:100])" 2>/dev/null); \
	if echo "$$RU_TEXT" | python3 -c "import sys; text=sys.stdin.read(); has_cyrillic=any('\u0400' <= c <= '\u04FF' for c in text); sys.exit(0 if has_cyrillic else 1)" 2>/dev/null; then \
		echo -e "  $(GREEN)PASS$(NC)  кириллица в ответе: \"$$RU_TEXT\""; \
	else \
		echo -e "  $(YELLOW)WARN$(NC)  нет кириллицы: \"$$RU_TEXT\""; \
	fi; \
	\
	TOTAL=$$((TOTAL+1)); \
	echo "8. max_tokens (ограничение ответа)"; \
	curl -s -o /tmp/vllm-test-maxtok.json --max-time 60 \
		-X POST "$(TEST_URL)/v1/chat/completions" \
		-H 'Content-Type: application/json' \
		-d '{"model":"$(VLLM_MODEL)","messages":[{"role":"user","content":"Напиши длинный текст про историю России"}],"temperature":0,"max_tokens":10}'; \
	OUT_TOK=$$(python3 -c "import json; d=json.load(open('/tmp/vllm-test-maxtok.json')); print(d.get('usage',{}).get('completion_tokens',0))" 2>/dev/null); \
	if [ "$$OUT_TOK" -le 10 ] && [ "$$OUT_TOK" -gt 0 ]; then \
		echo -e "  $(GREEN)PASS$(NC)  ответ обрезан: $$OUT_TOK токенов (запрошено max_tokens=10)"; \
	else \
		echo -e "  $(YELLOW)WARN$(NC)  completion_tokens=$$OUT_TOK (ожидалось <=10)"; \
	fi; \
	\
	TOTAL=$$((TOTAL+1)); \
	echo "9. Ошибка: несуществующая модель"; \
	STATUS=$$(curl -s -o /tmp/vllm-test-err.json -w '%{http_code}' --max-time 15 \
		-X POST "$(TEST_URL)/v1/chat/completions" \
		-H 'Content-Type: application/json' \
		-d '{"model":"nonexistent-model-xyz","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'); \
	if [ "$$STATUS" != "200" ]; then \
		ERR_MSG=$$(python3 -c "import json; d=json.load(open('/tmp/vllm-test-err.json')); print(d.get('error',{}).get('message','')[:80])" 2>/dev/null || echo "код $$STATUS"); \
		echo -e "  $(GREEN)PASS$(NC)  $$STATUS  ошибка возвращена: $$ERR_MSG"; \
	else \
		echo -e "  $(RED)FAIL$(NC)  $$STATUS  ожидалась ошибка"; \
		FAILED=$$((FAILED+1)); \
	fi; \
	\
	echo ""; \
	echo -e "$(BOLD)$(CYAN)=== Бенчмарк производительности ===$(NC)"; \
	echo ""; \
	python3 bench.py "$(TEST_URL)/v1/chat/completions" "$(VLLM_MODEL)" "$(VLLM_BENCH_ITERATIONS)" "$(VLLM_BENCH_CONCURRENCY)"; \
	\
	echo ""; \
	echo "=========================================="; \
	printf "$(BOLD)Test results: %d/%d passed$(NC)" $$((TOTAL - FAILED)) $$TOTAL; \
	if [ $$FAILED -gt 0 ]; then \
		printf " $(RED)(%d failed)$(NC)" $$FAILED; \
	else \
		printf " $(GREEN)— all green$(NC)"; \
	fi; \
	echo ""; \
	echo "=========================================="; \
	\
	if [ "$$USE_EXISTING" = "0" ]; then \
		echo ""; \
		echo "[cleanup] Stopping test server..."; \
		docker rm -f "vllm-test-$$$$" 2>/dev/null || true; \
	fi; \
	\
	exit $$FAILED

bench:
	@if ! curl -s --max-time 2 "$(VLLM_URL)/health" > /dev/null 2>&1; then \
		echo "Сервер не запущен. Запустите: make run"; \
		exit 1; \
	fi
	python3 bench.py "$(VLLM_URL)/v1/chat/completions" "$(VLLM_MODEL)" "$(VLLM_BENCH_ITERATIONS)" "$(VLLM_BENCH_CONCURRENCY)"

clean:
	@echo "=== Удаление контейнера ==="
	-docker stop "$(VLLM_CONTAINER_NAME)" 2>/dev/null
	-docker rm "$(VLLM_CONTAINER_NAME)" 2>/dev/null
	@echo "Готово"

clean-all:
	@echo "=== Удаление контейнера и кэша моделей ==="
	-docker stop "$(VLLM_CONTAINER_NAME)" 2>/dev/null
	-docker rm "$(VLLM_CONTAINER_NAME)" 2>/dev/null
	@if [ -d "$(VLLM_MODELS_DIR_ABS)" ]; then \
		echo "Удаление $(VLLM_MODELS_DIR_ABS)..."; \
		rm -rf "$(VLLM_MODELS_DIR_ABS)"; \
	fi
	@echo "Готово"
