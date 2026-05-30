#!/usr/bin/env bash
set -euo pipefail

docker_dir="${1:?docker dir is required}"
env_file="${2:?env file is required}"

if [[ ! -d "$docker_dir" ]]; then
  echo "Каталог upstream docker не найден: $docker_dir"
  exit 1
fi

if [[ -f "$env_file" ]]; then
  echo "Upstream docker .env уже существует: $env_file"
  exit 0
fi

if [[ -f "$docker_dir/.env.example" ]]; then
  cp "$docker_dir/.env.example" "$env_file"
elif [[ -f "$docker_dir/env.example" ]]; then
  cp "$docker_dir/env.example" "$env_file"
elif [[ -f "$docker_dir/.env" ]]; then
  cp "$docker_dir/.env" "$env_file"
else
  touch "$env_file"
fi

echo "Создан upstream docker .env: $env_file"
echo "Проверьте его перед продакшен-использованием. Настройки model-провайдеров задаются в ragflow/.env."
