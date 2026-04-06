#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

. "$ROOT_DIR/scripts/port_state.sh"

mkdir -p artifacts
: > artifacts/signals.jsonl
: > artifacts/portfolio.jsonl

cleanup() {
  if [[ -n "${SQL_CLIENT_PID:-}" ]] && kill -0 "$SQL_CLIENT_PID" >/dev/null 2>&1; then
    kill "$SQL_CLIENT_PID" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT

cleanup_partial_compose_state
resolve_runtime_ports
save_runtime_ports

uv --directory app sync --group dev
docker compose up -d --build redpanda jobmanager taskmanager
./scripts/wait_for_infra.sh
./scripts/create_topics.sh

docker compose exec -T jobmanager /bin/bash -lc "/opt/flink/bin/sql-client.sh -f /opt/flink/sql/market_features.sql" \
  > artifacts/flink-submit.log 2>&1 &
SQL_CLIENT_PID=$!

sleep 8

uv --directory app run strategy-service --max-messages 6 > artifacts/strategy.log 2>&1 &
STRATEGY_PID=$!

uv --directory app run portfolio-service --max-messages 6 > artifacts/portfolio.log 2>&1 &
PORTFOLIO_PID=$!

sleep 3
uv --directory app run replay-market --csv "$ROOT_DIR/data/sample/btcusdt_ticks.csv" --speedup 50

wait "$STRATEGY_PID"
wait "$PORTFOLIO_PID"

echo "signals written to artifacts/signals.jsonl"
echo "portfolio written to artifacts/portfolio.jsonl"
