SHELL := /bin/bash
export PATH := /opt/local/bin:$(PATH)
UV ?= $(shell command -v uv 2>/dev/null || echo /Users/damir/.langflow/uv/uv)

ROOT_DIR := ..
ROOT_ENV_FILE := $(ROOT_DIR)/.env
ENV_FILE := .env

ifneq (,$(wildcard $(ROOT_ENV_FILE)))
include $(ROOT_ENV_FILE)
export
endif

ifneq (,$(wildcard $(ENV_FILE)))
include $(ENV_FILE)
export
endif

APP_HOST ?= 0.0.0.0
APP_PORT ?= 8000
POSTGRES_PORT ?= 5432
DATABASE_URL ?= postgresql+psycopg://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@localhost:$(POSTGRES_PORT)/$(POSTGRES_DB)
DOCKER ?= docker
DOCKER_IMAGE ?= findoctor-backend:local
DOCKER_CONTAINER ?= findoctor-backend
DOCKER_HOST_PORT ?= 8001
DOCKER_APP_PORT ?= 8000
DOCKER_DB_HOST ?= host.docker.internal

.PHONY: help init init-env deploy-local deploy-cloud stop status logs shell db-up db-start db-stop db-logs db-psql migrate migration rollback db-current db-history run test test-unit test-auth test-accounts test-comprehensive test-all test-verbose test-debug test-coverage lint compile contract-check test-db-reset docker-build docker-up docker-run docker-stop docker-logs docker-shell docker-smoke docker-clean frontend-tunnel frontend-tunnel-stop backend-tunnel backend-tunnel-stop

help:
	@echo "Commands:"
	@echo ""
	@echo "  Setup:"
	@echo "    make init                 Alias for init-env"
	@echo "    make init-env             Create backend .env from .env.example if needed"
	@echo ""
	@echo "  Application:"
	@echo "    make run                  Start FastAPI dev server on $(APP_HOST):$(APP_PORT)"
	@echo ""
	@echo "  Standard deployment:"
	@echo "    make deploy-local         Build/run backend container against local PostgreSQL"
	@echo "    make deploy-cloud         Validate cloud/external backend configuration"
	@echo "    make stop                 Stop backend container"
	@echo "    make status               Show backend container status"
	@echo "    make logs                 Follow backend container logs"
	@echo ""
	@echo "  Docker backend:"
	@echo "    make docker-build         Build backend image from this directory"
	@echo "    make docker-up            Build and run backend container"
	@echo "    make docker-run           Run backend container against local PostgreSQL"
	@echo "    make docker-smoke         Check public reference endpoint through container"
	@echo "    make docker-logs          Follow backend container logs"
	@echo "    make docker-shell         Open shell inside backend container"
	@echo "    make docker-stop          Stop and remove backend container"
	@echo ""
	@echo "  Database:"
	@echo "    make db-up                Start local PostgreSQL container"
	@echo "    make db-start             Start existing PostgreSQL container"
	@echo "    make db-stop              Stop PostgreSQL container"
	@echo "    make db-logs              Follow PostgreSQL logs"
	@echo "    make db-psql              Open psql inside the container"
	@echo ""
	@echo "  Migrations:"
	@echo "    make migrate              Apply all migrations"
	@echo "    make migration m='msg'    Create empty Alembic migration"
	@echo "    make rollback             Roll back one migration"
	@echo "    make db-current           Show current Alembic revision"
	@echo "    make db-history           Show Alembic migration history"
	@echo ""
	@echo "  Testing:"
	@echo "    make test                 Run full local test gate"
	@echo "    make test-unit            Run pytest only"
	@echo "    make test-auth           Run authentication tests only"
	@echo "    make test-accounts       Run accounts tests only"
	@echo "    make test-comprehensive  Run comprehensive tests with database verification"
	@echo "    make test-all            Run all tests including comprehensive ones"
	@echo "    make test-verbose        Run tests with verbose output"
	@echo "    make test-debug          Run tests with debug output"
	@echo "    make test-coverage       Run tests with coverage report"
	@echo "    make lint                Run ruff linter"
	@echo "    make compile             Compile Python files"
	@echo "    make contract-check      Check FastAPI routes against OpenAPI contract"
	@echo ""
	@echo "  Frontend Tunnel:"
	@echo "    make frontend-tunnel     Start frontend server with ngrok tunnel for remote access"
	@echo "    make frontend-tunnel-stop Stop frontend tunnel processes"
	@echo "    make backend-tunnel      Start backend server with ngrok tunnel for remote API access"
	@echo "    make backend-tunnel-stop Stop backend tunnel processes"

init-env:
	@test -f $(ENV_FILE) || cp .env.example $(ENV_FILE)
	@echo "Env-файл готов: $(ENV_FILE)"

init: init-env

deploy-local: init-env docker-up docker-smoke

deploy-cloud: init-env
	@test -n "$(DATABASE_URL)" || { echo "DATABASE_URL не задан"; exit 1; }
	@test -n "$(JWT_SECRET_KEY)" || { echo "JWT_SECRET_KEY не задан"; exit 1; }
	@echo "Cloud backend config OK: DATABASE_URL and JWT_SECRET_KEY are present."

stop: docker-stop

status:
	@$(DOCKER) ps -a --filter "name=$(DOCKER_CONTAINER)" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

logs: docker-logs

shell: docker-shell

db-up:
	mkdir -p $(ROOT_DIR)/db/postgres-data
	@if docker ps -a --format '{{.Names}}' | grep -qx 'findoctor-postgres'; then \
		docker start findoctor-postgres; \
	else \
		docker run -d \
			--name findoctor-postgres \
			--env-file $(ENV_FILE) \
			-p "$(POSTGRES_PORT):5432" \
			-v "$$(cd $(ROOT_DIR) && pwd)/db/postgres-data:/var/lib/postgresql/data" \
			postgres:16-alpine; \
	fi

db-start:
	docker start findoctor-postgres

db-stop:
	docker stop findoctor-postgres

db-logs:
	docker logs -f findoctor-postgres

db-psql:
	docker exec -it findoctor-postgres psql -U "$(POSTGRES_USER)" -d "$(POSTGRES_DB)"

migrate:
	DATABASE_URL="$(DATABASE_URL)" $(UV) run alembic upgrade head

migration:
	@test -n "$(m)" || (echo "Usage: make migration m='create table name'" && exit 1)
	DATABASE_URL="$(DATABASE_URL)" $(UV) run alembic revision -m "$(m)"

rollback:
	DATABASE_URL="$(DATABASE_URL)" $(UV) run alembic downgrade -1

db-current:
	DATABASE_URL="$(DATABASE_URL)" $(UV) run alembic current

db-history:
	DATABASE_URL="$(DATABASE_URL)" $(UV) run alembic history

run:
	@echo "Starting on http://$(APP_HOST):$(APP_PORT)"
	$(UV) run uvicorn app.main:app --host $(APP_HOST) --port $(APP_PORT) --reload

docker-build:
	$(DOCKER) build -t $(DOCKER_IMAGE) .

docker-up: docker-build docker-run

docker-run: docker-stop
	$(DOCKER) run -d \
		--name $(DOCKER_CONTAINER) \
		--env-file $(ENV_FILE) \
		-e APP_HOST=0.0.0.0 \
		-e APP_PORT=$(DOCKER_APP_PORT) \
		-e POSTGRES_HOST=$(DOCKER_DB_HOST) \
		-e POSTGRES_PORT=$(POSTGRES_PORT) \
		-e DATABASE_URL=postgresql+psycopg://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@$(DOCKER_DB_HOST):$(POSTGRES_PORT)/$(POSTGRES_DB) \
		-e RUN_MIGRATIONS=true \
		-p $(DOCKER_HOST_PORT):$(DOCKER_APP_PORT) \
		--add-host=host.docker.internal:host-gateway \
		$(DOCKER_IMAGE)
	@echo "Backend container: http://localhost:$(DOCKER_HOST_PORT)/api/v1"

docker-stop:
	-$(DOCKER) rm -f $(DOCKER_CONTAINER) >/dev/null 2>&1

docker-logs:
	$(DOCKER) logs -f $(DOCKER_CONTAINER)

docker-shell:
	$(DOCKER) exec -it $(DOCKER_CONTAINER) sh

docker-smoke:
	@for attempt in $$(seq 1 30); do \
		if curl -fsS http://localhost:$(DOCKER_HOST_PORT)/api/v1/reference/account-types >/dev/null; then \
			echo "OK: backend container отвечает на /api/v1/reference/account-types"; \
			exit 0; \
		fi; \
		sleep 1; \
	done; \
	echo "Backend container не ответил за 30 секунд. Проверьте: make docker-logs"; \
	exit 1

docker-clean: docker-stop
	-$(DOCKER) rmi $(DOCKER_IMAGE) >/dev/null 2>&1

test:
	$(MAKE) lint
	$(MAKE) compile
	$(MAKE) test-db-reset
	$(MAKE) test-unit

test-unit:
	$(UV) run pytest tests/ -v

test-auth:
	$(MAKE) test-db-reset
	$(UV) run pytest tests/test_auth.py tests/test_auth_comprehensive.py -v

test-accounts:
	$(MAKE) test-db-reset
	$(UV) run pytest tests/test_accounts.py -v

test-comprehensive:
	$(MAKE) test-db-reset
	$(UV) run pytest tests/test_auth_comprehensive.py -v

test-all:
	$(MAKE) test

test-verbose:
	$(UV) run pytest tests/ -vv

test-debug:
	$(UV) run pytest tests/ -vvv --capture=no

test-coverage:
	$(MAKE) test-db-reset
	$(UV) run pytest tests/ --cov=app --cov-report=html --cov-report=term

lint:
	$(UV) run ruff check app tests scripts

compile:
	$(UV) run python -m compileall -q app tests scripts

contract-check:
	$(UV) run pytest tests/test_openapi_contract.py -v

test-db-reset:
	$(UV) run python scripts/reset_test_db.py

frontend-tunnel:
	@echo "=== Setting up frontend tunnel for remote access ==="
	@echo ""
	@echo "1. Checking frontend directory..."
	@if [ ! -d "$(ROOT_DIR)/frontend" ]; then \
		echo "Error: Frontend directory not found at $(ROOT_DIR)/frontend"; \
		exit 1; \
	fi
	@if [ ! -f "$(ROOT_DIR)/frontend/index.html" ]; then \
		echo "Creating simple test index.html..."; \
		echo '<!DOCTYPE html><html><head><title>FinDoctor Test</title></head><body><h1>FinDoctor Frontend Test</h1><p>If you can see this, the tunnel is working!</p></body></html>' > "$(ROOT_DIR)/frontend/index.html"; \
	fi
	@echo "✓ Frontend directory ready"
	@echo ""
	@echo "2. Starting local HTTP server on port 5173..."
	@if pgrep -f "python3.*http.server.*5173" > /dev/null; then \
		echo "Warning: Python HTTP server already running on port 5173"; \
	else \
		cd "$(ROOT_DIR)/frontend" && python3 -m http.server 5173 --bind 0.0.0.0 > /dev/null 2>&1 & \
		echo "✓ HTTP server started in background (PID: $$!)"; \
		SERVER_PID=$$!; \
	fi
	@echo ""
	@echo "3. Verifying local access..."
	@sleep 2
	@if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5173/ | grep -q "200"; then \
		echo "✓ Local server responding (HTTP 200)"; \
	else \
		echo "Error: Local server not responding"; \
		exit 1; \
	fi
	@echo ""
	@echo "4. Checking for tunnel tools and starting tunnel..."
	@TUNNEL_TOOL=""; \
	if command -v ngrok > /dev/null 2>&1; then \
		echo "✓ ngrok found at $$(command -v ngrok)"; \
		TUNNEL_TOOL="ngrok"; \
	elif command -v cloudflared > /dev/null 2>&1; then \
		echo "✓ cloudflared found (ngrok not available, using cloudflared)"; \
		TUNNEL_TOOL="cloudflared"; \
	else \
		echo "Error: Neither ngrok nor cloudflared found. Install one of them:"; \
		echo "  ngrok: brew install ngrok/ngrok/ngrok"; \
		echo "  cloudflared: brew install cloudflare/cloudflare/cloudflared"; \
		exit 1; \
	fi; \
	echo ""; \
	echo "5. Starting tunnel..."; \
	if [ "$$TUNNEL_TOOL" = "ngrok" ]; then \
		if pgrep -f "ngrok http 5173" > /dev/null; then \
			echo "Warning: ngrok tunnel already running"; \
			echo "Check ngrok dashboard at: http://127.0.0.1:4040 for the URL"; \
			PUBLIC_URL="http://127.0.0.1:4040 (check dashboard)"; \
		else \
			echo "Starting ngrok tunnel..."; \
			echo ""; \
			echo "=== IMPORTANT: NGROK WILL RUN IN THIS TERMINAL ==="; \
			echo "The ngrok URL will appear below. Look for a line like:"; \
			echo "  url=https://xxxxxx.ngrok-free.dev"; \
			echo ""; \
			echo "Once you see the URL, you can:"; \
			echo "1. Copy the URL (starts with https://)"; \
			echo "2. Send it to the other machine"; \
			echo "3. Press Ctrl+C to stop ngrok when done"; \
			echo ""; \
			echo "=== NGROK OUTPUT STARTS BELOW ==="; \
			echo ""; \
			ngrok http 5173 --log stdout; \
			echo ""; \
			echo "=== NGROK STOPPED ==="; \
			PUBLIC_URL="See ngrok output above for URL"; \
		fi; \
	elif [ "$$TUNNEL_TOOL" = "cloudflared" ]; then \
		echo "Starting cloudflared tunnel..."; \
		cloudflared tunnel --url http://127.0.0.1:5173 & \
		CLOUDFLARED_PID=$$!; \
		echo "✓ Cloudflared started (PID: $$CLOUDFLARED_PID)"; \
		echo "Waiting for cloudflared URL (10 seconds)..."; \
		sleep 10; \
		echo "Cloudflared URL usually appears in its output above."; \
		echo "Look for a *.trycloudflare.com URL in the output."; \
		PUBLIC_URL="https://*.trycloudflare.com (check output above)"; \
	fi
	@echo ""
	@echo "7. Verifying public URL..."
	@if [ "$$TUNNEL_TOOL" = "ngrok" ] && [ -n "$$PUBLIC_URL" ]; then \
		if curl -s -o /dev/null -w "%{http_code}" "$$PUBLIC_URL" | grep -q "200"; then \
			echo "✓ Public URL accessible (HTTP 200)"; \
		else \
			echo "Warning: Public URL may not be accessible yet"; \
		fi; \
	fi
	@echo ""
	@echo "=== TUNNEL SETUP COMPLETE ==="
	@echo ""
	@echo "Public URL: $$PUBLIC_URL"
	@echo ""
	@echo "Send this URL to the other machine for testing."
	@echo "The tunnel will stay active until you stop it with:"
	@echo "  make frontend-tunnel-stop"
	@echo ""
	@echo "Or manually kill processes:"
	@echo "  pkill -f 'python3.*http.server.*5173'"
	@echo "  pkill -f 'ngrok http 5173'  # or pkill -f cloudflared"
	@echo ""
	@echo "Note: Keep this terminal open or the tunnel will stop."

frontend-tunnel-stop:
	@echo "=== Stopping frontend tunnel processes ==="
	@if pgrep -f "python3.*http.server.*5173" > /dev/null; then \
		pkill -f "python3.*http.server.*5173"; \
		echo "✓ Stopped Python HTTP server"; \
	else \
		echo "Python HTTP server not running"; \
	fi
	@if pgrep -f "ngrok http 5173" > /dev/null; then \
		pkill -f "ngrok http 5173"; \
		echo "✓ Stopped ngrok tunnel"; \
	fi
	@if pgrep -f "cloudflared.*tunnel.*5173" > /dev/null; then \
		pkill -f "cloudflared.*tunnel.*5173"; \
		echo "✓ Stopped cloudflared tunnel"; \
	fi
	@echo "=== All tunnel processes stopped ==="

backend-tunnel:
	@echo "=== Setting up backend tunnel for remote API access ==="
	@echo ""
	@echo "1. Starting backend server on port $(APP_PORT)..."
	@if pgrep -f "uvicorn.*app.main:app.*$(APP_PORT)" > /dev/null; then \
		echo "Warning: Backend server already running on port $(APP_PORT)"; \
	else \
		$(UV) run uvicorn app.main:app --host $(APP_HOST) --port $(APP_PORT) --reload > /dev/null 2>&1 & \
		echo "✓ Backend server started in background (PID: $$!)"; \
		SERVER_PID=$$!; \
	fi
	@echo ""
	@echo "2. Verifying local access..."
	@sleep 3
	@if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$(APP_PORT)/docs | grep -q "200"; then \
		echo "✓ Backend server responding (HTTP 200)"; \
	else \
		echo "Error: Backend server not responding"; \
		exit 1; \
	fi
	@echo ""
	@echo "3. Checking for tunnel tools and starting tunnel..."
	@TUNNEL_TOOL=""; \
	if command -v ngrok > /dev/null 2>&1; then \
		echo "✓ ngrok found at $$(command -v ngrok)"; \
		TUNNEL_TOOL="ngrok"; \
	elif command -v cloudflared > /dev/null 2>&1; then \
		echo "✓ cloudflared found (ngrok not available, using cloudflared)"; \
		TUNNEL_TOOL="cloudflared"; \
	else \
		echo "Error: Neither ngrok nor cloudflared found. Install one of them:"; \
		echo "  ngrok: brew install ngrok/ngrok/ngrok"; \
		echo "  cloudflared: brew install cloudflare/cloudflare/cloudflared"; \
		exit 1; \
	fi; \
	echo ""; \
	echo "4. Starting tunnel..."; \
	if [ "$$TUNNEL_TOOL" = "ngrok" ]; then \
		if pgrep -f "ngrok http $(APP_PORT)" > /dev/null; then \
			echo "Warning: ngrok tunnel already running"; \
			echo "Check ngrok dashboard at: http://127.0.0.1:4040 for the URL"; \
			PUBLIC_URL="http://127.0.0.1:4040 (check dashboard)"; \
		else \
			echo "Starting ngrok tunnel..."; \
			echo ""; \
			echo "=== IMPORTANT: NGROK WILL RUN IN THIS TERMINAL ==="; \
			echo "The ngrok URL will appear below. Look for a line like:"; \
			echo "  url=https://xxxxxx.ngrok-free.dev"; \
			echo ""; \
			echo "Once you see the URL, you can:"; \
			echo "1. Copy the URL (starts with https://)"; \
			echo "2. Send it to the other machine"; \
			echo "3. Press Ctrl+C to stop ngrok when done"; \
			echo ""; \
			echo "=== NGROK OUTPUT STARTS BELOW ==="; \
			echo ""; \
			ngrok http $(APP_PORT) --log stdout; \
			echo ""; \
			echo "=== NGROK STOPPED ==="; \
			PUBLIC_URL="See ngrok output above for URL"; \
		fi; \
	elif [ "$$TUNNEL_TOOL" = "cloudflared" ]; then \
		echo "Starting cloudflared tunnel..."; \
		cloudflared tunnel --url http://127.0.0.1:$(APP_PORT) & \
		CLOUDFLARED_PID=$$!; \
		echo "✓ Cloudflared started (PID: $$CLOUDFLARED_PID)"; \
		echo "Waiting for cloudflared URL (10 seconds)..."; \
		sleep 10; \
		echo "Cloudflared URL usually appears in its output above."; \
		echo "Look for a *.trycloudflare.com URL in the output."; \
		PUBLIC_URL="https://*.trycloudflare.com (check output above)"; \
	fi
	@echo ""
	@echo "6. Verifying public URL..."
	@if [ "$$TUNNEL_TOOL" = "ngrok" ] && [ -n "$$PUBLIC_URL" ]; then \
		if curl -s -o /dev/null -w "%{http_code}" "$$PUBLIC_URL/docs" | grep -q "200"; then \
			echo "✓ Public URL accessible (HTTP 200)"; \
		else \
			echo "Warning: Public URL may not be accessible yet"; \
		fi; \
	fi
	@echo ""
	@echo "=== BACKEND TUNNEL SETUP COMPLETE ==="
	@echo ""
	@echo "Public API URL: $$PUBLIC_URL"
	@echo "API Documentation: $$PUBLIC_URL/docs"
	@echo ""
	@echo "Send these URLs to the other machine for testing."
	@echo "The tunnel will stay active until you stop it with:"
	@echo "  make backend-tunnel-stop"
	@echo ""
	@echo "Or manually kill processes:"
	@echo "  pkill -f 'uvicorn.*app.main:app.*$(APP_PORT)'"
	@echo "  pkill -f 'ngrok http $(APP_PORT)'  # or pkill -f cloudflared"
	@echo ""
	@echo "Note: Keep this terminal open or the tunnel will stop."

backend-tunnel-stop:
	@echo "=== Stopping backend tunnel processes ==="
	@if pgrep -f "uvicorn.*app.main:app.*$(APP_PORT)" > /dev/null; then \
		pkill -f "uvicorn.*app.main:app.*$(APP_PORT)"; \
		echo "✓ Stopped backend server"; \
	else \
		echo "Backend server not running"; \
	fi
	@if pgrep -f "ngrok http $(APP_PORT)" > /dev/null; then \
		pkill -f "ngrok http $(APP_PORT)"; \
		echo "✓ Stopped ngrok tunnel"; \
	fi
	@if pgrep -f "cloudflared.*tunnel.*$(APP_PORT)" > /dev/null; then \
		pkill -f "cloudflared.*tunnel.*$(APP_PORT)"; \
		echo "✓ Stopped cloudflared tunnel"; \
	fi
	@echo "=== All backend tunnel processes stopped ==="
