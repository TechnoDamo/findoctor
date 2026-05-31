SHELL := /bin/bash
export PATH := /opt/local/bin:$(PATH)

ENV_FILE ?= .env

ifneq (,$(wildcard $(ENV_FILE)))
include $(ENV_FILE)
export
endif

DOCKER ?= docker
FRONTEND_IMAGE ?= findoctor-frontend:local
FRONTEND_CONTAINER ?= findoctor-frontend
FRONTEND_HOST_PORT ?= 3000
FRONTEND_APP_PORT ?= 3000
NEXT_PUBLIC_API_URL ?= http://localhost:8001
NEXT_PUBLIC_DEFAULT_LOCALE ?= ru
NEXT_PUBLIC_DEFAULT_CURRENCY ?= RUB
NEXT_PUBLIC_DEFAULT_TIMEZONE ?= Europe/Moscow

.PHONY: help init deploy-local deploy-cloud build run stop logs status shell test docker-build docker-run docker-stop docker-clean

help:
	@echo "Frontend ПрофИИта"
	@echo ""
	@echo "  make init           Подготовить frontend .env, если есть .env.example"
	@echo "  make deploy-local   Собрать и запустить frontend container"
	@echo "  make deploy-cloud   Проверить cloud-конфигурацию frontend"
	@echo "  make build          Собрать Next.js production build локально"
	@echo "  make run            Запустить Next.js dev server"
	@echo "  make test           npm audit + production build"
	@echo "  make stop           Остановить frontend container"
	@echo "  make logs           Смотреть логи frontend container"
	@echo "  make status         Показать статус frontend container"

init:
	@test -f $(ENV_FILE) || { test ! -f .env.example || cp .env.example $(ENV_FILE); }
	@echo "frontend/.env готов"

deploy-local: init docker-build docker-run
	@echo "Frontend container: http://localhost:$(FRONTEND_HOST_PORT)"

deploy-cloud:
	@test -n "$(NEXT_PUBLIC_API_URL)" || { echo "NEXT_PUBLIC_API_URL не задан"; exit 1; }
	@echo "Cloud frontend config OK: NEXT_PUBLIC_API_URL=$(NEXT_PUBLIC_API_URL)"

build:
	npm run build

run:
	npm run dev

test:
	npm audit --audit-level=moderate
	npm run build

docker-build:
	$(DOCKER) build \
		--build-arg NEXT_PUBLIC_API_URL="$(NEXT_PUBLIC_API_URL)" \
		--build-arg NEXT_PUBLIC_DEFAULT_LOCALE="$(NEXT_PUBLIC_DEFAULT_LOCALE)" \
		--build-arg NEXT_PUBLIC_DEFAULT_CURRENCY="$(NEXT_PUBLIC_DEFAULT_CURRENCY)" \
		--build-arg NEXT_PUBLIC_DEFAULT_TIMEZONE="$(NEXT_PUBLIC_DEFAULT_TIMEZONE)" \
		-t "$(FRONTEND_IMAGE)" .

docker-run: docker-stop
	$(DOCKER) run -d \
		--name "$(FRONTEND_CONTAINER)" \
		-e PORT="$(FRONTEND_APP_PORT)" \
		-e NEXT_PUBLIC_API_URL="$(NEXT_PUBLIC_API_URL)" \
		-p "$(FRONTEND_HOST_PORT):$(FRONTEND_APP_PORT)" \
		"$(FRONTEND_IMAGE)"

stop docker-stop:
	-$(DOCKER) rm -f "$(FRONTEND_CONTAINER)" >/dev/null 2>&1

logs:
	$(DOCKER) logs -f "$(FRONTEND_CONTAINER)"

status:
	@$(DOCKER) ps -a --filter "name=$(FRONTEND_CONTAINER)" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

shell:
	$(DOCKER) exec -it "$(FRONTEND_CONTAINER)" sh

docker-clean: docker-stop
	-$(DOCKER) rmi "$(FRONTEND_IMAGE)" >/dev/null 2>&1
