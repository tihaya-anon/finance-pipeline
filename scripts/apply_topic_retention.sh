#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

RETENTION_MS="${1:-86400000}"

for topic in market_ticks market_features trade_signals portfolio_snapshots; do
  docker compose exec -T redpanda rpk topic alter-config "$topic" --set "retention.ms=${RETENTION_MS}"
done

echo "Applied retention.ms=${RETENTION_MS} to development topics."
