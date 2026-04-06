#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

pkill -f "uv --directory app run strategy-service" >/dev/null 2>&1 || true
pkill -f "uv --directory app run portfolio-service" >/dev/null 2>&1 || true
pkill -f "uv --directory app run questdb-sink" >/dev/null 2>&1 || true
pkill -f "uv --directory app run stream-binance" >/dev/null 2>&1 || true

docker compose down --remove-orphans

echo "Finance pipeline stack stopped."
