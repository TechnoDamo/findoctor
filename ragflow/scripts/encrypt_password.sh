#!/usr/bin/env bash
set -euo pipefail
docker exec docker-ragflow-cpu-1 python3 -c "import sys; sys.path.insert(0,\"/ragflow\"); from api.utils.crypt import crypt; print(crypt(\"${1}\"))" 2>/dev/null
