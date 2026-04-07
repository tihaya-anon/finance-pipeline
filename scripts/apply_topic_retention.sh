#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

. "$ROOT_DIR/scripts/config_env.sh"
load_config_env

RETENTION_MS="${1:-$DEV_TOPIC_RETENTION_MS}"

for topic in market_ticks market_features trade_signals portfolio_snapshots; do
  docker compose exec -T redpanda rpk topic alter-config "$topic" --set "retention.ms=${RETENTION_MS}"
done

echo "Applied retention.ms=${RETENTION_MS} to development topics."
