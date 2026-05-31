SHELL := /bin/bash
export PATH := /opt/local/bin:$(PATH)

ENV_FILE ?= .env

ifneq (,$(wildcard $(ENV_FILE)))
include $(ENV_FILE)
export
endif

GRAYLOG_HTTP_PORT ?= 9001
GRAYLOG_GELF_UDP_PORT ?= 12201
GRAYLOG_GELF_TCP_PORT ?= 12201
GRAYLOG_API_URL ?= http://localhost:$(GRAYLOG_HTTP_PORT)
GRAYLOG_ROOT_USERNAME ?= admin
GRAYLOG_ROOT_PASSWORD ?= admin
GRAYLOG_INPUT_TITLE ?= FinDoctor Backend GELF UDP

.PHONY: help init init-env deploy-local deploy-cloud up down stop restart logs status ps wait input input-udp streams configure test-input reset-old

help:
	@echo "Graylog commands:"
	@echo "  make init           Alias for init-env"
	@echo "  make deploy-local   Start and configure local Graylog stack"
	@echo "  make deploy-cloud   Validate external Graylog/GELF config"
	@echo "  make init-env       Create graylog/.env from .env.example"
	@echo "  make up             Start Graylog, MongoDB, and Elasticsearch"
	@echo "  make down           Stop the Graylog stack"
	@echo "  make restart        Restart the Graylog stack"
	@echo "  make logs           Follow Graylog logs"
	@echo "  make status         Show container status"
	@echo "  make wait           Wait until Graylog API is reachable"
	@echo "  make input          Create GELF TCP input for backend logs"
	@echo "  make input-udp      Create GELF UDP input for backend logs"
	@echo "  make streams        Create FinDoctor streams and rules"
	@echo "  make configure      Wait, create input, and create streams"
	@echo "  make reset-old      Stop/remove old generic Graylog containers"
	@echo "  make test-input     Send a test GELF message"

init-env:
	@test -f .env || cp .env.example .env
	@echo "graylog/.env is ready"

init: init-env

deploy-local: init-env up configure

deploy-cloud:
	@test -n "$(GRAYLOG_HOST)" || { echo "GRAYLOG_HOST не задан — укажите external Graylog/GELF endpoint в graylog/.env"; exit 1; }
	@if echo "$(GRAYLOG_HOST)" | grep -Eq 'localhost|127\.0\.0\.1|host\.docker\.internal'; then \
		echo "GRAYLOG_HOST выглядит локальным, а DEPLOYMENT=cloud ожидает external log endpoint."; \
		exit 1; \
	fi
	@echo "Cloud Graylog config OK: $(GRAYLOG_HOST)"

up:
	docker compose --env-file $(ENV_FILE) up -d

down:
	docker compose --env-file $(ENV_FILE) down

stop: down

restart:
	docker compose --env-file $(ENV_FILE) restart

logs:
	docker compose --env-file $(ENV_FILE) logs -f graylog

status ps:
	docker compose --env-file $(ENV_FILE) ps

wait:
	@for i in {1..120}; do \
		code=$$(curl -sS -o /dev/null -w '%{http_code}' "$(GRAYLOG_API_URL)/api/system" \
			-u "$(GRAYLOG_ROOT_USERNAME):$(GRAYLOG_ROOT_PASSWORD)" \
			-H 'X-Requested-By: findoctor' || true); \
		if [[ "$$code" == "200" ]]; then echo "Graylog is ready"; exit 0; fi; \
		sleep 2; \
	done; \
	echo "Graylog API was not ready at $(GRAYLOG_API_URL)"; exit 1

reset-old:
	-docker rm -f graylog graylog-mongodb graylog-elasticsearch mimir-graylog-init

input:
	@if curl -sS -u "$(GRAYLOG_ROOT_USERNAME):$(GRAYLOG_ROOT_PASSWORD)" \
		-H 'X-Requested-By: findoctor' \
		"$(GRAYLOG_API_URL)/api/system/inputs" \
		| python3 -c 'import json,os,sys; port=int(os.environ.get("GRAYLOG_GELF_TCP_PORT","12201")); data=json.load(sys.stdin); raise SystemExit(0 if any(i.get("type")=="org.graylog2.inputs.gelf.tcp.GELFTCPInput" and i.get("attributes",{}).get("port")==port for i in data.get("inputs", [])) else 1)'; then \
		echo "GELF TCP input already exists on port $(GRAYLOG_GELF_TCP_PORT)"; \
	else \
		curl -sS -u "$(GRAYLOG_ROOT_USERNAME):$(GRAYLOG_ROOT_PASSWORD)" \
			-H 'Content-Type: application/json' \
			-H 'X-Requested-By: findoctor' \
			-X POST "$(GRAYLOG_API_URL)/api/system/inputs" \
			-d '{"title":"$(GRAYLOG_INPUT_TITLE)","type":"org.graylog2.inputs.gelf.tcp.GELFTCPInput","global":true,"configuration":{"bind_address":"0.0.0.0","port":$(GRAYLOG_GELF_TCP_PORT),"recv_buffer_size":1048576,"max_message_size":2097152,"override_source":null,"decompress_size_limit":8388608},"node":null}'; \
		echo; \
	fi

input-udp:
	@if curl -sS -u "$(GRAYLOG_ROOT_USERNAME):$(GRAYLOG_ROOT_PASSWORD)" \
		-H 'X-Requested-By: findoctor' \
		"$(GRAYLOG_API_URL)/api/system/inputs" \
		| python3 -c 'import json,os,sys; port=int(os.environ.get("GRAYLOG_GELF_UDP_PORT","12201")); data=json.load(sys.stdin); raise SystemExit(0 if any(i.get("type")=="org.graylog2.inputs.gelf.udp.GELFUDPInput" and i.get("attributes",{}).get("port")==port for i in data.get("inputs", [])) else 1)'; then \
		echo "GELF UDP input already exists on port $(GRAYLOG_GELF_UDP_PORT)"; \
	else \
		curl -sS -u "$(GRAYLOG_ROOT_USERNAME):$(GRAYLOG_ROOT_PASSWORD)" \
			-H 'Content-Type: application/json' \
			-H 'X-Requested-By: findoctor' \
			-X POST "$(GRAYLOG_API_URL)/api/system/inputs" \
			-d '{"title":"FinDoctor Backend GELF UDP","type":"org.graylog2.inputs.gelf.udp.GELFUDPInput","global":true,"configuration":{"bind_address":"0.0.0.0","port":$(GRAYLOG_GELF_UDP_PORT),"recv_buffer_size":262144,"override_source":null,"decompress_size_limit":8388608},"node":null}'; \
		echo; \
	fi

test-input:
	printf '{"version":"1.1","host":"findoctor-local","short_message":"findoctor graylog test","level":6,"facility":"findoctor-backend"}\0' | nc -w1 localhost $(GRAYLOG_GELF_TCP_PORT)

streams:
	python3 scripts/configure_streams.py

configure: wait input streams
