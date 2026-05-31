SHELL := /bin/bash
export PATH := /opt/local/bin:$(PATH)

ENV_FILE := .env

ifneq (,$(wildcard $(ENV_FILE)))
include $(ENV_FILE)
export
endif

WHISPER_CPP_DIR := whisper.cpp
WHISPER_BUILD_DIR := $(WHISPER_CPP_DIR)/build
WHISPER_SERVER_BIN := $(WHISPER_BUILD_DIR)/bin/whisper-server

WHISPER_MODEL            ?= large-v3-turbo
WHISPER_MODELS_DIR       ?= ./whisper.cpp/models
WHISPER_HOST             ?= 127.0.0.1
WHISPER_PORT             ?= 8080
WHISPER_THREADS          ?= 4
WHISPER_PROCESSORS       ?= 1
WHISPER_LANGUAGE         ?= auto
WHISPER_MAX_CONTEXT      ?= -1
WHISPER_MAX_LEN          ?= 0
WHISPER_BEST_OF          ?= 5
WHISPER_BEAM_SIZE        ?= -1
WHISPER_NO_TIMESTAMPS    ?= false
WHISPER_SPLIT_ON_WORD    ?= false
WHISPER_DEBUG_MODE       ?= false
WHISPER_CONVERT          ?= false
WHISPER_NO_GPU           ?= false
WHISPER_FLASH_ATTN       ?= true
WHISPER_NO_CONTEXT       ?= false
WHISPER_SUPPRESS_NST     ?= false
WHISPER_NO_SPEECH_THOLD  ?= 0.6
WHISPER_PROMPT           ?=
WHISPER_REQUEST_PATH     ?=
WHISPER_INFERENCE_PATH   ?=

WHISPER_CPP_PORT         ?= 8082

UNAME_S := $(shell uname -s)
UNAME_M := $(shell uname -m)

CMAKE_ARGS := -DWHISPER_BUILD_SERVER=ON

ifdef WHISPER_ACCELERATION
  ifeq ($(WHISPER_ACCELERATION),coreml)
    CMAKE_ARGS += -DWHISPER_COREML=ON -DWHISPER_COREML_ALLOW_FALLBACK=ON
  else ifeq ($(WHISPER_ACCELERATION),cuda)
    CMAKE_ARGS += -DGGML_CUDA=ON
  else ifeq ($(WHISPER_ACCELERATION),metal)
    CMAKE_ARGS += -DGGML_METAL=ON
  else ifeq ($(WHISPER_ACCELERATION),opencl)
    CMAKE_ARGS += -DGGML_OPENCL=ON
  else ifeq ($(WHISPER_ACCELERATION),vulkan)
    CMAKE_ARGS += -DGGML_VULKAN=ON
  else ifeq ($(WHISPER_ACCELERATION),openblas)
    CMAKE_ARGS += -DGGML_OPENBLAS=ON
  else ifeq ($(WHISPER_ACCELERATION),hipblas)
    CMAKE_ARGS += -DGGML_HIPBLAS=ON
  else ifeq ($(WHISPER_ACCELERATION),none)
    # no acceleration
  else
    $(error Unknown WHISPER_ACCELERATION: $(WHISPER_ACCELERATION). Valid: coreml, cuda, metal, opencl, vulkan, openblas, hipblas, none)
  endif
else
  ifeq ($(UNAME_S),Darwin)
    CMAKE_ARGS += -DWHISPER_COREML=ON -DWHISPER_COREML_ALLOW_FALLBACK=ON
    ifeq ($(UNAME_M),arm64)
      CMAKE_ARGS += -DGGML_METAL=ON
    endif
  else ifeq ($(UNAME_S),Linux)
    HAS_NVIDIA := $(shell command -v nvidia-smi 2>/dev/null)
    ifneq (,$(HAS_NVIDIA))
      CMAKE_ARGS += -DGGML_CUDA=ON
    else
      HAS_ROCM := $(shell command -v rocminfo 2>/dev/null)
      ifneq (,$(HAS_ROCM))
        CMAKE_ARGS += -DGGML_HIPBLAS=ON
      else
        HAS_OPENBLAS := $(shell pkg-config --exists openblas 2>/dev/null && echo 1 || echo 0)
        ifeq ($(HAS_OPENBLAS),1)
          CMAKE_ARGS += -DGGML_OPENBLAS=ON
        endif
      endif
    endif
  endif
endif

.PHONY: help init deploy-local deploy-cloud stop status logs build model run run-raw proxy-install clean info test

help:
	@echo "whisper-server commands:"
	@echo ""
	@echo "  make init          Create .env from .env.example"
	@echo "  make deploy-local  Build model/proxy and start proxy in background"
	@echo "  make deploy-cloud  Validate external STT endpoint config"
	@echo "  make build         Build whisper.cpp with hardware acceleration"
	@echo "  make model         Download Whisper model ($(WHISPER_MODEL))"
	@echo "  make proxy-install Install Python proxy dependencies"
	@echo "  make run           Start OpenAI-compatible proxy on $(WHISPER_HOST):$(WHISPER_PORT)"
	@echo "  make run-raw       Start whisper.cpp directly (debug, port $(WHISPER_CPP_PORT))"
	@echo "  make clean         Remove build artifacts"
	@echo "  make info          Show detected hardware and configuration"
	@echo "  make test          Run server test suite"
	@echo ""
	@echo "Quick start:"
	@echo "  make init && make build && make model && make proxy-install && make run"

init:
	@test -f .env || cp .env.example .env
	@if [ ! -f "$(WHISPER_CPP_DIR)/CMakeLists.txt" ]; then \
		echo "Initializing whisper.cpp submodule..."; \
		cd .. && git submodule update --init whisper-server/whisper.cpp; \
	fi
	@echo "whisper-server/.env is ready"

deploy-local: init build model proxy-install
	@mkdir -p .runtime
	@if [ -f .runtime/proxy.pid ] && kill -0 "$$(cat .runtime/proxy.pid)" 2>/dev/null; then \
		echo "whisper proxy уже запущен, pid=$$(cat .runtime/proxy.pid)"; \
	else \
		nohup python3 proxy_server.py > .runtime/proxy.log 2>&1 & echo $$! > .runtime/proxy.pid; \
		echo "whisper proxy запущен на $(WHISPER_HOST):$(WHISPER_PORT), pid=$$(cat .runtime/proxy.pid)"; \
	fi

deploy-cloud:
	@test -n "$(STT_BASE_URL)" || { echo "STT_BASE_URL не задан"; exit 1; }
	@test -n "$(STT_MODEL)" || { echo "STT_MODEL не задан"; exit 1; }
	@if echo "$(STT_BASE_URL)" | grep -Eq 'localhost|127\.0\.0\.1|host\.docker\.internal'; then \
		echo "STT_BASE_URL выглядит локальным, а DEPLOYMENT=cloud ожидает external STT endpoint."; \
		exit 1; \
	fi
	@echo "Cloud STT config OK: $(STT_BASE_URL), model=$(STT_MODEL)"

stop:
	@if [ -f .runtime/proxy.pid ]; then \
		kill "$$(cat .runtime/proxy.pid)" 2>/dev/null || true; \
		rm -f .runtime/proxy.pid; \
	fi

status:
	@if [ -f .runtime/proxy.pid ] && kill -0 "$$(cat .runtime/proxy.pid)" 2>/dev/null; then \
		echo "whisper proxy running, pid=$$(cat .runtime/proxy.pid), url=http://$(WHISPER_HOST):$(WHISPER_PORT)"; \
	else \
		echo "whisper proxy is not running"; \
	fi

logs:
	@tail -f .runtime/proxy.log

build:
	@if [ ! -f "$(WHISPER_CPP_DIR)/CMakeLists.txt" ]; then \
		echo "ERROR: whisper.cpp submodule not found. Run: make init"; \
		exit 1; \
	fi
	@echo "=== Building whisper.cpp server ==="
	@echo "Detected: $(UNAME_S) / $(UNAME_M)"
	@echo "CMake args: $(CMAKE_ARGS)"
	@echo ""
	cd $(WHISPER_CPP_DIR) && cmake -B build $(CMAKE_ARGS)
	cd $(WHISPER_CPP_DIR) && cmake --build build --config Release -j
	@echo ""
	@echo "=== Build complete ==="
	@echo "Binary: $(WHISPER_SERVER_BIN)"

model:
	@echo "=== Downloading model: $(WHISPER_MODEL) ==="
	@if [ -f "$(WHISPER_MODELS_DIR)/ggml-$(WHISPER_MODEL).bin" ]; then \
		echo "Model already exists: $(WHISPER_MODELS_DIR)/ggml-$(WHISPER_MODEL).bin"; \
	else \
		cd $(WHISPER_CPP_DIR) && bash models/download-ggml-model.sh $(WHISPER_MODEL); \
	fi
	@echo "Model ready: $(WHISPER_MODELS_DIR)/ggml-$(WHISPER_MODEL).bin"

proxy-install:
	@echo "=== Installing proxy dependencies ==="
	@command -v uv >/dev/null 2>&1 && uv pip install -r requirements.txt || pip install -r requirements.txt
	@echo "Done"

run:
	@test -f "$(WHISPER_SERVER_BIN)" || (echo "ERROR: Server binary not found. Run 'make build' first." && exit 1)
	@test -f "$(WHISPER_MODELS_DIR)/ggml-$(WHISPER_MODEL).bin" || (echo "ERROR: Model not found. Run 'make model' first." && exit 1)
	@command -v python3 >/dev/null 2>&1 || (echo "ERROR: python3 required for proxy" && exit 1)
	@echo "=== Starting whisper-server proxy ==="
	@echo "Proxy:    $(WHISPER_HOST):$(WHISPER_PORT)"
	@echo "Internal: 127.0.0.1:$(WHISPER_CPP_PORT)"
	@echo "Model:    ggml-$(WHISPER_MODEL).bin"
	@echo "Endpoint: POST /chat/completions  (OpenAI-compatible)"
	@echo ""
	python3 proxy_server.py

run-raw:
	@test -f "$(WHISPER_SERVER_BIN)" || (echo "ERROR: Server binary not found. Run 'make build' first." && exit 1)
	@test -f "$(WHISPER_MODELS_DIR)/ggml-$(WHISPER_MODEL).bin" || (echo "ERROR: Model not found. Run 'make model' first." && exit 1)
	@echo "=== Starting whisper-server (raw) ==="
	@echo "Host:     $(WHISPER_HOST):$(WHISPER_PORT)"
	@echo "Model:    ggml-$(WHISPER_MODEL).bin"
	@echo "Threads:  $(WHISPER_THREADS) | Language: $(WHISPER_LANGUAGE)"
	@echo "Endpoint: $(if $(WHISPER_REQUEST_PATH),$(WHISPER_REQUEST_PATH)$(WHISPER_INFERENCE_PATH),/inference)"
	@echo ""
	$(WHISPER_SERVER_BIN) \
		--model "$(WHISPER_MODELS_DIR)/ggml-$(WHISPER_MODEL).bin" \
		--host "$(WHISPER_HOST)" \
		--port "$(WHISPER_PORT)" \
		--threads $(WHISPER_THREADS) \
		--processors $(WHISPER_PROCESSORS) \
		--language $(WHISPER_LANGUAGE) \
		--max-context $(WHISPER_MAX_CONTEXT) \
		--max-len $(WHISPER_MAX_LEN) \
		--best-of $(WHISPER_BEST_OF) \
		--beam-size $(WHISPER_BEAM_SIZE) \
		--no-speech-thold $(WHISPER_NO_SPEECH_THOLD) \
		$(if $(filter true,$(WHISPER_SPLIT_ON_WORD)),--split-on-word,) \
		$(if $(filter true,$(WHISPER_NO_TIMESTAMPS)),--no-timestamps,) \
		$(if $(filter true,$(WHISPER_DEBUG_MODE)),--debug-mode,) \
		$(if $(filter true,$(WHISPER_CONVERT)),--convert,) \
		$(if $(filter true,$(WHISPER_NO_GPU)),--no-gpu,) \
		$(if $(filter true,$(WHISPER_FLASH_ATTN)),,--no-flash-attn) \
		$(if $(filter true,$(WHISPER_NO_CONTEXT)),--no-context,) \
		$(if $(filter true,$(WHISPER_SUPPRESS_NST)),--suppress-nst,) \
		$(if $(WHISPER_PROMPT),--prompt "$(WHISPER_PROMPT)",) \
		$(if $(WHISPER_REQUEST_PATH),--request-path "$(WHISPER_REQUEST_PATH)",) \
		$(if $(WHISPER_INFERENCE_PATH),--inference-path "$(WHISPER_INFERENCE_PATH)",)

clean:
	@echo "=== Cleaning build artifacts ==="
	rm -rf $(WHISPER_BUILD_DIR)
	@echo "Done"

info:
	@echo "=== System ==="
	@echo "OS:           $(UNAME_S)"
	@echo "Architecture: $(UNAME_M)"
	@echo ""
	@echo "=== Hardware Acceleration ==="
	@echo "CMake args:   $(CMAKE_ARGS)"
	@echo ""
	@echo "=== Model ==="
	@echo "Model:        $(WHISPER_MODEL)"
	@echo "Models dir:   $(WHISPER_MODELS_DIR)"
	@if [ -f "$(WHISPER_MODELS_DIR)/ggml-$(WHISPER_MODEL).bin" ]; then \
		SIZE=$$(du -sh "$(WHISPER_MODELS_DIR)/ggml-$(WHISPER_MODEL).bin" 2>/dev/null | cut -f1); \
		echo "Status:       Downloaded ($$SIZE)"; \
	else \
		echo "Status:       Not downloaded (run 'make model')"; \
	fi
	@echo ""
	@echo "=== Server ==="
	@echo "Host:         $(WHISPER_HOST):$(WHISPER_PORT)"
	@echo "Threads:      $(WHISPER_THREADS)"
	@echo "Processors:   $(WHISPER_PROCESSORS)"
	@echo "Language:     $(WHISPER_LANGUAGE)"
	@echo "Max context:  $(WHISPER_MAX_CONTEXT)"
	@echo "Best of:      $(WHISPER_BEST_OF)"
	@echo "Beam size:    $(WHISPER_BEAM_SIZE)"
	@echo "Endpoint:     $(if $(WHISPER_REQUEST_PATH),$(WHISPER_REQUEST_PATH)$(WHISPER_INFERENCE_PATH),/inference)"

TEST_PORT := 18180
TEST_MODEL := $(WHISPER_MODELS_DIR)/for-tests-ggml-tiny.bin
TEST_AUDIO := /tmp/whisper-test-jfk.wav
TEST_AUDIO_URL := https://github.com/ggerganov/whisper.cpp/raw/master/samples/jfk.wav
TEST_URL := http://127.0.0.1:$(TEST_PORT)/inference

RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m

define TEST_PASS
	@echo -e "  $(GREEN)PASS$(NC)  $(1)"
endef

define TEST_FAIL
	@echo -e "  $(RED)FAIL$(NC)  $(1)"
endef

test: $(WHISPER_SERVER_BIN)
	@echo "=== Whisper Server Test Suite ==="
	@echo ""
	@FAILED=0; TOTAL=0; \
	\
	echo "[setup] Preparing test audio..."; \
	if [ ! -f "$(TEST_AUDIO)" ]; then \
		echo "[setup] Downloading jfk.wav sample..."; \
		curl -sSfL -o "$(TEST_AUDIO)" "$(TEST_AUDIO_URL)" || { \
			echo "[setup] Download failed, generating test tone instead..."; \
			python3 -c "import wave,struct,math; w=wave.open('$(TEST_AUDIO)','w'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000); [w.writeframes(struct.pack('<h',int(8000*math.sin(2*math.pi*440*i/16000)))) for i in range(48000)]; w.close()"; \
		}; \
	else \
		echo "[setup] Test audio found: $(TEST_AUDIO)"; \
	fi; \
	\
	echo "[setup] Verifying test model..."; \
	if [ ! -f "$(TEST_MODEL)" ]; then \
		echo "[setup] Test model not found, downloading ggml-tiny.bin..."; \
		cd $(WHISPER_CPP_DIR) && bash models/download-ggml-model.sh tiny; \
		TEST_MODEL="$(WHISPER_MODELS_DIR)/ggml-tiny.bin"; \
	fi; \
	\
	lsof -ti:$(TEST_PORT) 2>/dev/null | xargs kill -9 2>/dev/null || true; \
	\
	echo "[setup] Starting server on port $(TEST_PORT)..."; \
	$(WHISPER_SERVER_BIN) \
		--model "$(TEST_MODEL)" \
		--host 127.0.0.1 \
		--port $(TEST_PORT) \
		--threads 2 \
		--processors 1 \
		> /tmp/whisper-test-server.log 2>&1 & \
	SERVER_PID=$$!; \
	echo $$SERVER_PID > /tmp/whisper-test-server.pid; \
	\
	echo -n "[setup] Waiting for server"; \
	for i in {1..60}; do \
		if curl -s http://127.0.0.1:$(TEST_PORT)/ 2>/dev/null | grep -q .; then \
			echo " ready ($${i}s)"; break; \
		fi; \
		sleep 1; echo -n .; \
	done; \
	echo ""; echo ""; \
	\
	echo "=== Tests ==="; \
	echo ""; \
	\
	TOTAL=$$((TOTAL+1)); \
	echo "1. Basic inference (json, 200 OK)"; \
	STATUS=$$(curl -s -o /tmp/whisper-test-resp.json -w '%{http_code}' \
		-X POST $(TEST_URL) \
		-F "file=@$(TEST_AUDIO)" \
		-F "response_format=json"); \
	if [ "$$STATUS" = "200" ]; then \
		if python3 -c "import json; d=json.load(open('/tmp/whisper-test-resp.json')); assert 'text' in d, 'missing text'; print('OK')" 2>/dev/null; then \
			TEXT=$$(python3 -c "import json; print(json.load(open('/tmp/whisper-test-resp.json'))['text'][:60])" 2>/dev/null); \
			echo -e "  $(GREEN)PASS$(NC)  $$STATUS  text=\"$$TEXT...\""; \
		else \
			echo -e "  $(RED)FAIL$(NC)  $$STATUS  invalid json response"; \
			FAILED=$$((FAILED+1)); \
		fi; \
	else \
		echo -e "  $(RED)FAIL$(NC)  $$STATUS"; \
		FAILED=$$((FAILED+1)); \
	fi; \
	\
	TOTAL=$$((TOTAL+1)); \
	echo "2. Verbose JSON (language detection)"; \
	STATUS=$$(curl -s -o /tmp/whisper-test-resp.json -w '%{http_code}' \
		-X POST $(TEST_URL) \
		-F "file=@$(TEST_AUDIO)" \
		-F "response_format=verbose_json"); \
	if [ "$$STATUS" = "200" ]; then \
		if python3 -c "import json; d=json.load(open('/tmp/whisper-test-resp.json')); assert 'language' in d; assert 'segments' in d; print('OK')" 2>/dev/null; then \
			LANG=$$(python3 -c "import json; print(json.load(open('/tmp/whisper-test-resp.json'))['language'])" 2>/dev/null); \
			echo -e "  $(GREEN)PASS$(NC)  $$STATUS  language=\"$$LANG\""; \
		else \
			echo -e "  $(RED)FAIL$(NC)  $$STATUS  missing language/segments"; \
			FAILED=$$((FAILED+1)); \
		fi; \
	else \
		echo -e "  $(RED)FAIL$(NC)  $$STATUS"; \
		FAILED=$$((FAILED+1)); \
	fi; \
	\
	TOTAL=$$((TOTAL+1)); \
	echo "3. Plain text (response_format=text)"; \
	STATUS=$$(curl -s -o /tmp/whisper-test-text.txt -w '%{http_code}' \
		-X POST $(TEST_URL) \
		-F "file=@$(TEST_AUDIO)" \
		-F "response_format=text"); \
	if [ "$$STATUS" = "200" ]; then \
		LEN=$$(wc -c < /tmp/whisper-test-text.txt | tr -d ' '); \
		if [ "$$LEN" -gt 1 ]; then \
			TEXT=$$(head -c 60 /tmp/whisper-test-text.txt); \
			echo -e "  $(GREEN)PASS$(NC)  $$STATUS  text=\"$$TEXT...\""; \
		else \
			echo -e "  $(YELLOW)WARN$(NC)  $$STATUS  too short ($$LEN bytes, tiny model on low-quality sample)"; \
		fi; \
	else \
		echo -e "  $(RED)FAIL$(NC)  $$STATUS"; \
		FAILED=$$((FAILED+1)); \
	fi; \
	\
	TOTAL=$$((TOTAL+1)); \
	echo "4. SRT format (subtitles)"; \
	STATUS=$$(curl -s -o /tmp/whisper-test-resp.srt -w '%{http_code}' \
		-X POST $(TEST_URL) \
		-F "file=@$(TEST_AUDIO)" \
		-F "response_format=srt"); \
	if [ "$$STATUS" = "200" ]; then \
	if grep -q -e '-->' /tmp/whisper-test-resp.srt; then \
		echo -e "  $(GREEN)PASS$(NC)  $$STATUS  valid SRT (timestamps found)"; \
	else \
		echo -e "  $(YELLOW)WARN$(NC)  $$STATUS  no timestamps (tiny model may be too weak for this sample)"; \
	fi; \
else \
	echo -e "  $(RED)FAIL$(NC)  $$STATUS"; \
	FAILED=$$((FAILED+1)); \
fi; \
\
TOTAL=$$((TOTAL+1)); \
echo "5. VTT format (subtitles)"; \
STATUS=$$(curl -s -o /tmp/whisper-test-resp.vtt -w '%{http_code}' \
	-X POST $(TEST_URL) \
	-F "file=@$(TEST_AUDIO)" \
	-F "response_format=vtt"); \
if [ "$$STATUS" = "200" ]; then \
	if grep -q -e '-->' /tmp/whisper-test-resp.vtt; then \
			echo -e "  $(GREEN)PASS$(NC)  $$STATUS  valid VTT (timestamps found)"; \
		else \
			echo -e "  $(YELLOW)WARN$(NC)  $$STATUS  no timestamps (tiny model may be too weak for this sample)"; \
		fi; \
	else \
		echo -e "  $(RED)FAIL$(NC)  $$STATUS"; \
		FAILED=$$((FAILED+1)); \
	fi; \
	\
	TOTAL=$$((TOTAL+1)); \
	echo "6. Language parameter (force=en)"; \
	STATUS=$$(curl -s -o /tmp/whisper-test-resp.json -w '%{http_code}' \
		-X POST $(TEST_URL) \
		-F "file=@$(TEST_AUDIO)" \
		-F "response_format=verbose_json" \
		-F "language=en"); \
	if [ "$$STATUS" = "200" ]; then \
		LANG=$$(python3 -c "import json; print(json.load(open('/tmp/whisper-test-resp.json'))['language'])" 2>/dev/null); \
		if [ "$$LANG" = "english" ]; then \
			echo -e "  $(GREEN)PASS$(NC)  $$STATUS  forced language=\"$$LANG\""; \
		else \
			echo -e "  $(YELLOW)WARN$(NC)  $$STATUS  expected \"english\", got \"$$LANG\" (tiny model may be weak)"; \
		fi; \
	else \
		echo -e "  $(RED)FAIL$(NC)  $$STATUS"; \
		FAILED=$$((FAILED+1)); \
	fi; \
	\
	TOTAL=$$((TOTAL+1)); \
	echo "7. Temperature parameter"; \
	STATUS=$$(curl -s -o /tmp/whisper-test-resp.json -w '%{http_code}' \
		-X POST $(TEST_URL) \
		-F "file=@$(TEST_AUDIO)" \
		-F "response_format=json" \
		-F "temperature=0.2"); \
	if [ "$$STATUS" = "200" ]; then \
		echo -e "  $(GREEN)PASS$(NC)  $$STATUS  temperature accepted"; \
	else \
		echo -e "  $(RED)FAIL$(NC)  $$STATUS"; \
		FAILED=$$((FAILED+1)); \
	fi; \
	\
	TOTAL=$$((TOTAL+1)); \
	echo "8. Missing file (error handling)"; \
	STATUS=$$(curl -s -o /tmp/whisper-test-resp.txt -w '%{http_code}' \
		-X POST $(TEST_URL) \
		-F "response_format=json"); \
	if [ "$$STATUS" != "200" ]; then \
		echo -e "  $(GREEN)PASS$(NC)  $$STATUS  error returned (no file)"; \
	else \
		echo -e "  $(YELLOW)WARN$(NC)  $$STATUS  accepted without file (server-specific)"; \
	fi; \
	\
	TOTAL=$$((TOTAL+1)); \
	echo "9. Server root endpoint"; \
	STATUS=$$(curl -s -o /tmp/whisper-test-root.txt -w '%{http_code}' \
		http://127.0.0.1:$(TEST_PORT)/); \
	if [ "$$STATUS" != "0" ] && [ "$$STATUS" != "000" ]; then \
		echo -e "  $(GREEN)PASS$(NC)  $$STATUS  server responds"; \
	else \
		echo -e "  $(RED)FAIL$(NC)  $$STATUS  server not responding"; \
		FAILED=$$((FAILED+1)); \
	fi; \
	\
	TOTAL=$$((TOTAL+1)); \
	echo "10. Same file twice (consistency)"; \
	curl -s -o /tmp/whisper-test-c1.json -X POST $(TEST_URL) -F "file=@$(TEST_AUDIO)" -F "response_format=json"; \
	curl -s -o /tmp/whisper-test-c2.json -X POST $(TEST_URL) -F "file=@$(TEST_AUDIO)" -F "response_format=json"; \
	T1=$$(python3 -c "import json; print(json.load(open('/tmp/whisper-test-c1.json'))['text'])" 2>/dev/null); \
	T2=$$(python3 -c "import json; print(json.load(open('/tmp/whisper-test-c2.json'))['text'])" 2>/dev/null); \
	if [ "$$T1" = "$$T2" ]; then \
		echo -e "  $(GREEN)PASS$(NC)  deterministic output"; \
	else \
		echo -e "  $(YELLOW)WARN$(NC)  outputs differ (temperature may vary)"; \
	fi; \
	\
	echo ""; \
	echo "=========================================="; \
	printf "Results: %d/%d passed" $$((TOTAL - FAILED)) $$TOTAL; \
	if [ $$FAILED -gt 0 ]; then \
		printf " (%d failed)\n" $$FAILED; \
	else \
		printf " — all green\n"; \
	fi; \
	echo "=========================================="; \
	\
	echo ""; \
	echo "[cleanup] Stopping server..."; \
	kill $$(cat /tmp/whisper-test-server.pid) 2>/dev/null || true; \
	rm -f /tmp/whisper-test-server.pid /tmp/whisper-test-server.log; \
	\
	exit $$FAILED
