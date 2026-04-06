#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

for topic in portfolio_snapshots trade_signals market_features market_ticks; do
  docker compose exec -T redpanda rpk topic delete "$topic" >/dev/null 2>&1 || true
done

./scripts/create_topics.sh
rm -f artifacts/*.jsonl artifacts/*.log
touch artifacts/.gitkeep

for table in portfolio_snapshots trade_signals market_features; do
  curl -fsS -G --data-urlencode "query=DROP TABLE IF EXISTS ${table}" "http://127.0.0.1:9000/exec" >/dev/null 2>&1 || true
done

echo "Development topics and artifacts reset."
