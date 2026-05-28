#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

. "$ROOT_DIR/scripts/lib/port_state.sh"

SERVICE_PID_FILE="$ROOT_DIR/artifacts/service-pids.env"

if [[ -f "$SERVICE_PID_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$SERVICE_PID_FILE"
  for pid_name in STRATEGY_PID PORTFOLIO_PID QUESTDB_SINK_PID; do
    pid="${!pid_name:-}"
    [[ -n "$pid" ]] || continue
    kill "$pid" >/dev/null 2>&1 || true
  done
  rm -f "$SERVICE_PID_FILE"
fi

pkill -f "scripts/python/strategy_service.py" >/dev/null 2>&1 || true
pkill -f "scripts/python/portfolio_service.py" >/dev/null 2>&1 || true
pkill -f "scripts/python/questdb_sink.py" >/dev/null 2>&1 || true
pkill -f "scripts/python/stream_binance.py" >/dev/null 2>&1 || true

docker compose down --remove-orphans >/dev/null 2>&1 || true

echo "Finance pipeline stack stopped."
