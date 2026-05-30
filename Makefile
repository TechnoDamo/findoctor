SHELL := /bin/zsh

FRONTEND_DIR ?= frontend
SHARE_PORT ?= 5173
SHARE_BIND ?= 0.0.0.0
SHARE_LOCAL_URL ?= http://127.0.0.1:$(SHARE_PORT)
FRONTEND_ORIGIN ?=
SHARE_STATE_DIR ?= tmp/frontend-share
SERVER_PID_FILE := $(SHARE_STATE_DIR)/server.pid
TUNNEL_PID_FILE := $(SHARE_STATE_DIR)/tunnel.pid
TUNNEL_PROVIDER_FILE := $(SHARE_STATE_DIR)/provider
PUBLIC_URL_FILE := $(SHARE_STATE_DIR)/public_url.txt
SERVER_LOG := $(SHARE_STATE_DIR)/server.log
TUNNEL_LOG := $(SHARE_STATE_DIR)/tunnel.log

.PHONY: frontend-share-help frontend-share-prepare frontend-share-server-up \
	frontend-share-server-check frontend-share-tunnel-up frontend-share-url \
	frontend-share-public-check frontend-share-up frontend-share-status frontend-share-down \
	frontend-share-install frontend-share-cloudflare-live frontend-share-frontend-deps

frontend-share-help:
	@echo "Temporary frontend remote access commands:"
	@echo "  make frontend-share-up           # prepare + local server + tunnel + verify public URL"
	@echo "  make frontend-share-cloudflare-live  # one-command live mode (recommended)"
	@echo "  make frontend-share-url          # print detected public URL"
	@echo "  make frontend-share-status       # show running processes and last URL"
	@echo "  make frontend-share-down         # stop local server and tunnel"
	@echo "  make frontend-share-install      # install ngrok/cloudflared via Homebrew if missing"
	@echo "  make frontend-share-frontend-deps # install frontend npm deps if missing"
	@echo ""
	@echo "Overrides:"
	@echo "  make frontend-share-up SHARE_PORT=5173 FRONTEND_DIR=frontend"
	@echo "  make frontend-share-cloudflare-live FRONTEND_ORIGIN=http://127.0.0.1:3000"

frontend-share-prepare:
	@mkdir -p "$(SHARE_STATE_DIR)"
	@if [ ! -d "$(FRONTEND_DIR)" ]; then \
		echo "ERROR: directory '$(FRONTEND_DIR)' does not exist"; \
		exit 1; \
	fi
	@if [ ! -f "$(FRONTEND_DIR)/index.html" ]; then \
		if [ -f "$(FRONTEND_DIR)/package.json" ] || [ -d "$(FRONTEND_DIR)/app" ] || [ -d "$(FRONTEND_DIR)/src" ]; then \
			echo "Frontend app detected in $(FRONTEND_DIR); skipping test index.html creation"; \
		else \
			echo "No frontend app detected, creating temporary $(FRONTEND_DIR)/index.html"; \
			printf '%s\n' \
				'<!doctype html>' \
				'<html lang="en">' \
				'<head>' \
				'  <meta charset="UTF-8">' \
				'  <meta name="viewport" content="width=device-width, initial-scale=1.0">' \
				'  <title>Frontend Remote Access Test</title>' \
				'  <style>' \
				'    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; background: #f7f7fb; color: #111; }' \
				'    .wrap { max-width: 760px; margin: 8vh auto; padding: 24px; background: #fff; border-radius: 14px; box-shadow: 0 10px 30px rgba(0,0,0,.08); }' \
				'    code { background: #f2f2f6; padding: 2px 6px; border-radius: 6px; }' \
				'  </style>' \
				'</head>' \
				'<body>' \
				'  <div class="wrap">' \
				'    <h1>Frontend remote access is working</h1>' \
				'    <p>This page was created automatically by <code>make frontend-share-prepare</code>.</p>' \
				'    <p>You can replace it with your real frontend page any time.</p>' \
				'  </div>' \
				'</body>' \
				'</html>' \
				> "$(FRONTEND_DIR)/index.html"; \
		fi; \
	fi

frontend-share-server-up: frontend-share-prepare
	@mkdir -p "$(SHARE_STATE_DIR)"
	@if [ -f "$(SERVER_PID_FILE)" ] && ps -p "$$(cat "$(SERVER_PID_FILE)")" >/dev/null 2>&1; then \
		echo "Local server already running with PID $$(cat "$(SERVER_PID_FILE)")"; \
	else \
		echo "Starting local static server on $(SHARE_LOCAL_URL)"; \
		cd "$(FRONTEND_DIR)" && nohup python3 -m http.server "$(SHARE_PORT)" --bind "$(SHARE_BIND)" > "../$(SERVER_LOG)" 2>&1 & \
		echo $$! > "../$(SERVER_PID_FILE)"; \
		sleep 1; \
	fi

frontend-share-server-check:
	@echo "Checking local URL: $(SHARE_LOCAL_URL)"
	@curl -I "$(SHARE_LOCAL_URL)"

frontend-share-tunnel-up: frontend-share-server-up
	@if [ -f "$(TUNNEL_PID_FILE)" ] && ! ps -p "$$(cat "$(TUNNEL_PID_FILE)")" >/dev/null 2>&1; then \
		rm -f "$(TUNNEL_PID_FILE)"; \
	fi
	@if [ -f "$(TUNNEL_PID_FILE)" ] && ps -p "$$(cat "$(TUNNEL_PID_FILE)")" >/dev/null 2>&1; then \
		echo "Tunnel already running with PID $$(cat "$(TUNNEL_PID_FILE)")"; \
		exit 0; \
	fi
	@if command -v ngrok >/dev/null 2>&1; then \
		echo "Starting ngrok tunnel"; \
		echo "ngrok" > "$(TUNNEL_PROVIDER_FILE)"; \
		nohup ngrok http "$(SHARE_PORT)" > "$(TUNNEL_LOG)" 2>&1 & \
		pid="$$!"; \
		echo "$$pid" > "$(TUNNEL_PID_FILE)"; \
		sleep 3; \
		if ! ps -p "$$pid" >/dev/null 2>&1; then \
			echo "ngrok failed to start. Recent log output:"; \
			tail -n 20 "$(TUNNEL_LOG)" || true; \
			if command -v cloudflared >/dev/null 2>&1; then \
				echo "Falling back to Cloudflare Tunnel"; \
				echo "cloudflared" > "$(TUNNEL_PROVIDER_FILE)"; \
				nohup cloudflared tunnel --url "$(SHARE_LOCAL_URL)" > "$(TUNNEL_LOG)" 2>&1 & \
				pid="$$!"; \
				echo "$$pid" > "$(TUNNEL_PID_FILE)"; \
				sleep 3; \
				if ! ps -p "$$pid" >/dev/null 2>&1; then \
					echo "ERROR: cloudflared also failed to start. See $(TUNNEL_LOG)"; \
					exit 1; \
				fi; \
			else \
				echo "ERROR: ngrok failed and cloudflared is not installed"; \
				exit 1; \
			fi; \
		fi; \
	elif command -v cloudflared >/dev/null 2>&1; then \
		echo "ngrok not found, starting Cloudflare Tunnel"; \
		echo "cloudflared" > "$(TUNNEL_PROVIDER_FILE)"; \
		nohup cloudflared tunnel --url "$(SHARE_LOCAL_URL)" > "$(TUNNEL_LOG)" 2>&1 & \
		pid="$$!"; \
		echo "$$pid" > "$(TUNNEL_PID_FILE)"; \
		sleep 3; \
		if ! ps -p "$$pid" >/dev/null 2>&1; then \
			echo "ERROR: cloudflared failed to start. See $(TUNNEL_LOG)"; \
			exit 1; \
		fi; \
	else \
		echo "ERROR: neither ngrok nor cloudflared is installed"; \
		exit 1; \
	fi

frontend-share-url:
	@mkdir -p "$(SHARE_STATE_DIR)"
	@provider="$$(cat "$(TUNNEL_PROVIDER_FILE)" 2>/dev/null || true)"; \
	url=""; \
	if [ "$$provider" = "ngrok" ]; then \
		i=0; \
		while [ $$i -lt 20 ]; do \
			url="$$(curl -s http://127.0.0.1:4040/api/tunnels | grep -o 'https://[^"]*' | head -n1)"; \
			[ -n "$$url" ] && break; \
			sleep 1; \
			i=$$((i + 1)); \
		done; \
		if [ -z "$$url" ] && grep -q "ERR_NGROK_" "$(TUNNEL_LOG)" 2>/dev/null; then \
			echo "ERROR: ngrok did not provide a public URL. Recent log output:"; \
			tail -n 20 "$(TUNNEL_LOG)" || true; \
		fi; \
	elif [ "$$provider" = "cloudflared" ]; then \
		i=0; \
		while [ $$i -lt 20 ]; do \
			url="$$(grep -o 'https://[-A-Za-z0-9.]*trycloudflare.com' "$(TUNNEL_LOG)" | tail -n1)"; \
			[ -n "$$url" ] && break; \
			sleep 1; \
			i=$$((i + 1)); \
		done; \
	fi; \
	if [ -z "$$url" ]; then \
		echo "ERROR: public URL not found yet. Check $(TUNNEL_LOG)"; \
		exit 1; \
	fi; \
	echo "$$url" | tee "$(PUBLIC_URL_FILE)"

frontend-share-public-check:
	@url="$$(cat "$(PUBLIC_URL_FILE)" 2>/dev/null || true)"; \
	if [ -z "$$url" ]; then \
		echo "ERROR: no saved public URL. Run 'make frontend-share-url'"; \
		exit 1; \
	fi; \
	echo "Checking public URL: $$url"; \
	curl -I "$$url"

frontend-share-up: frontend-share-server-up frontend-share-server-check frontend-share-tunnel-up frontend-share-url frontend-share-public-check
	@echo ""
	@echo "Remote access is ready."
	@echo "Share this URL with another machine:"
	@cat "$(PUBLIC_URL_FILE)"
	@echo ""
	@echo "Keep this running. When finished, stop with: make frontend-share-down"

frontend-share-status:
	@echo "Server PID file: $(SERVER_PID_FILE)"
	@if [ -f "$(SERVER_PID_FILE)" ]; then \
		pid="$$(cat "$(SERVER_PID_FILE)")"; \
		if ps -p "$$pid" >/dev/null 2>&1; then echo "Server running: PID $$pid"; else echo "Server not running"; fi; \
	else \
		echo "Server PID file missing"; \
	fi
	@echo "Tunnel PID file: $(TUNNEL_PID_FILE)"
	@if [ -f "$(TUNNEL_PID_FILE)" ]; then \
		pid="$$(cat "$(TUNNEL_PID_FILE)")"; \
		if ps -p "$$pid" >/dev/null 2>&1; then echo "Tunnel running: PID $$pid"; else echo "Tunnel not running"; fi; \
	else \
		echo "Tunnel PID file missing"; \
	fi
	@echo "Tunnel provider: $$(cat "$(TUNNEL_PROVIDER_FILE)" 2>/dev/null || echo unknown)"
	@echo "Last public URL: $$(cat "$(PUBLIC_URL_FILE)" 2>/dev/null || echo none)"
	@echo "Server log: $(SERVER_LOG)"
	@echo "Tunnel log: $(TUNNEL_LOG)"

frontend-share-down:
	@if [ -f "$(SERVER_PID_FILE)" ]; then \
		pid="$$(cat "$(SERVER_PID_FILE)")"; \
		if ps -p "$$pid" >/dev/null 2>&1; then kill "$$pid" && echo "Stopped server PID $$pid"; else echo "Server PID $$pid not running"; fi; \
		rm -f "$(SERVER_PID_FILE)"; \
	else \
		echo "Server is not running"; \
	fi
	@if [ -f "$(TUNNEL_PID_FILE)" ]; then \
		pid="$$(cat "$(TUNNEL_PID_FILE)")"; \
		if ps -p "$$pid" >/dev/null 2>&1; then kill "$$pid" && echo "Stopped tunnel PID $$pid"; else echo "Tunnel PID $$pid not running"; fi; \
		rm -f "$(TUNNEL_PID_FILE)"; \
	else \
		echo "Tunnel is not running"; \
	fi

frontend-share-install:
	@if ! command -v brew >/dev/null 2>&1; then \
		echo "ERROR: Homebrew is required. Install from https://brew.sh/"; \
		exit 1; \
	fi
	@if command -v ngrok >/dev/null 2>&1; then \
		echo "ngrok already installed: $$(command -v ngrok)"; \
	else \
		echo "Installing ngrok"; \
		brew install --cask ngrok; \
	fi
	@if command -v cloudflared >/dev/null 2>&1; then \
		echo "cloudflared already installed: $$(command -v cloudflared)"; \
	else \
		echo "Installing cloudflared"; \
		brew install cloudflared; \
	fi

frontend-share-frontend-deps:
	@set -e; \
	cd "$(FRONTEND_DIR)"; \
	if [ ! -f package.json ]; then \
		echo "ERROR: package.json not found in $(FRONTEND_DIR)"; \
		exit 1; \
	fi; \
	if npm ls framer-motion --depth=0 >/dev/null 2>&1; then \
		echo "Frontend dependencies are installed"; \
	else \
		echo "Installing frontend dependencies (framer-motion missing)"; \
		npm install; \
	fi

frontend-share-cloudflare-live: frontend-share-prepare
	@mkdir -p "$(SHARE_STATE_DIR)"
	@if ! command -v cloudflared >/dev/null 2>&1; then \
		echo "ERROR: cloudflared is not installed. Run: make frontend-share-install"; \
		exit 1; \
	fi
	@set -e; \
	cd "$(FRONTEND_DIR)"; \
	if [ -f package.json ] && grep -q '"next"' package.json; then \
		if ! npm ls framer-motion --depth=0 >/dev/null 2>&1; then \
			echo "Installing frontend dependencies (framer-motion missing)"; \
			npm install; \
		fi; \
	fi; \
	server_pid=""; \
	origin_url="$(SHARE_LOCAL_URL)"; \
	if [ -n "$(FRONTEND_ORIGIN)" ]; then \
		origin_url="$(FRONTEND_ORIGIN)"; \
	fi; \
	case "$$origin_url" in \
		http://127.0.0.1:*|http://localhost:*|https://127.0.0.1:*|https://localhost:*) ;; \
		*) \
			if echo "$$origin_url" | grep -Eqi 'ngrok|trycloudflare'; then \
				echo "ERROR: FRONTEND_ORIGIN points to public tunnel ($$origin_url)."; \
				echo "Set FRONTEND_ORIGIN to local Next.js origin, e.g. http://127.0.0.1:3000"; \
				exit 1; \
			fi; \
		;; \
	esac; \
	if [ -f package.json ] && grep -q '"next"' package.json; then \
		if [ -n "$(FRONTEND_ORIGIN)" ]; then \
			echo "Using explicit FRONTEND_ORIGIN=$$origin_url"; \
		elif curl -sI --max-time 2 http://127.0.0.1:3000/ | grep -qi 'X-Powered-By: Next.js'; then \
			origin_url="http://127.0.0.1:3000"; \
			echo "Detected running Next.js app at $$origin_url, reusing it"; \
		elif curl -sI --max-time 2 http://127.0.0.1:3001/ | grep -qi 'X-Powered-By: Next.js'; then \
			origin_url="http://127.0.0.1:3001"; \
			echo "Detected running Next.js app at $$origin_url, reusing it"; \
		elif curl -sI --max-time 2 "$(SHARE_LOCAL_URL)/" | grep -qi 'X-Powered-By: Next.js'; then \
			origin_url="$(SHARE_LOCAL_URL)"; \
			echo "Detected running Next.js app at $$origin_url, reusing it"; \
		else \
			echo "Detected Next.js app, starting: npm run dev -- --hostname $(SHARE_BIND) --port $(SHARE_PORT)"; \
			npm run dev -- --hostname "$(SHARE_BIND)" --port "$(SHARE_PORT)" > "../$(SERVER_LOG)" 2>&1 & \
			server_pid="$$!"; \
			echo "$$server_pid" > "../$(SERVER_PID_FILE)"; \
		fi; \
	else \
		echo "No Next.js detected, starting static server: python3 -m http.server $(SHARE_PORT) --bind $(SHARE_BIND)"; \
		python3 -m http.server "$(SHARE_PORT)" --bind "$(SHARE_BIND)" > "../$(SERVER_LOG)" 2>&1 & \
		server_pid="$$!"; \
		echo "$$server_pid" > "../$(SERVER_PID_FILE)"; \
	fi; \
	i=0; \
	until curl -sfI "$$origin_url" >/dev/null 2>&1; do \
		if [ -n "$$server_pid" ] && ! ps -p "$$server_pid" >/dev/null 2>&1; then \
			echo "ERROR: frontend process exited. Check $(SERVER_LOG)"; \
			exit 1; \
		fi; \
		if [ $$i -ge 60 ]; then \
			echo "ERROR: frontend did not become ready at $$origin_url. Check $(SERVER_LOG)"; \
			exit 1; \
		fi; \
		sleep 1; \
		i=$$((i + 1)); \
	done; \
	if [ -f package.json ] && grep -q '"next"' package.json; then \
		if ! curl -sI --max-time 3 "$$origin_url/" | grep -qi 'X-Powered-By: Next.js'; then \
			echo "ERROR: $$origin_url is reachable, but it does not look like Next.js."; \
			echo "This usually means tunnel points to backend/proxy port instead of frontend."; \
			echo "Tip: run with explicit origin, for example:"; \
			echo "  make frontend-share-cloudflare-live FRONTEND_ORIGIN=http://127.0.0.1:3000"; \
			exit 1; \
		fi; \
		if ! curl -sS -v --http1.1 --max-time 5 \
			-H 'Connection: Upgrade' \
			-H 'Upgrade: websocket' \
			-H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' \
			-H 'Sec-WebSocket-Version: 13' \
			"$$origin_url/_next/webpack-hmr" 2>&1 | grep -q '101 Switching Protocols'; then \
			echo "ERROR: $$origin_url/_next/webpack-hmr did not return WebSocket 101."; \
			echo "Tip: check local dev server and try explicit FRONTEND_ORIGIN."; \
			exit 1; \
		fi; \
	fi; \
	if [ -n "$$server_pid" ]; then \
		echo "Frontend is ready at $$origin_url (PID $$server_pid)"; \
	else \
		echo "Frontend is ready at $$origin_url (using existing process)"; \
	fi; \
	echo ""; \
	echo "Starting Cloudflare quick tunnel. Keep this terminal open."; \
	echo "Public URL will appear below in cloudflared output."; \
	if [ -n "$$server_pid" ]; then \
		trap 'kill "$$server_pid" 2>/dev/null || true' EXIT INT TERM; \
	fi; \
	env GODEBUG=netdns=cgo cloudflared tunnel --edge-ip-version 4 --url "$$origin_url"
