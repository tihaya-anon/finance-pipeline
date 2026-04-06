#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

for topic in market_ticks market_features trade_signals; do
  docker compose exec -T redpanda rpk topic create "$topic" >/dev/null 2>&1 || true
done

docker compose exec -T redpanda rpk topic list
