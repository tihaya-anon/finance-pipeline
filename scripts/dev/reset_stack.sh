#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

./scripts/dev/stop_stack.sh

docker compose down -v --remove-orphans >/dev/null 2>&1 || true

rm -f artifacts/*.jsonl artifacts/*.log
rm -f artifacts/service-pids.env
touch artifacts/.gitkeep

echo "Finance pipeline stack reset."
echo "Current preferred ports:"
make net
