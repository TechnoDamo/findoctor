#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Диагностика деплоя ФинДоктора"
echo ""

echo "Инструменты:"
for tool in docker curl python3; do
  if command -v "$tool" >/dev/null 2>&1; then
    echo "OK:   $tool -> $(command -v "$tool")"
  else
    echo "WARN: $tool не найден"
  fi
done

if command -v docker >/dev/null 2>&1; then
  if docker info >/dev/null 2>&1; then
    echo "OK:   Docker daemon доступен"
  else
    echo "WARN: Docker daemon недоступен"
  fi
fi

echo ""
echo "Backend:"
if [[ -x "$ROOT_DIR/backend/.venv/bin/python" ]]; then
  echo "OK:   backend/.venv существует"
else
  echo "WARN: backend/.venv не найден"
fi

if [[ -f "$ROOT_DIR/backend/.env" ]]; then
  echo "OK:   backend/.env существует"
else
  echo "WARN: backend/.env отсутствует; запустите make init-core"
fi

echo ""
echo "Recommendation-сервисы:"
for path in "$ROOT_DIR/tei/.env" "$ROOT_DIR/ragflow/.env" "$ROOT_DIR/searxng/.env"; do
  if [[ -f "$path" ]]; then
    echo "OK:   ${path#$ROOT_DIR/} существует"
  else
    echo "WARN: ${path#$ROOT_DIR/} отсутствует; запустите make init-recommendations"
  fi
done

echo ""
echo "Локальные контейнеры:"
docker ps -a \
  --filter "name=findoctor" \
  --filter "name=ragflow" \
  --filter "name=searxng" \
  --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || true
