#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

./scripts/stop_stack.sh

docker compose down -v --remove-orphans >/dev/null 2>&1 || true

rm -f artifacts/*.jsonl artifacts/*.log
touch artifacts/.gitkeep

echo "Finance pipeline stack reset."
echo "If you still have port conflicts, check local listeners with:"
echo "  ss -ltn | rg '39092|8080|8081|9000|9009|8812|3000'"
