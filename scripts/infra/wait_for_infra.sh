#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

. "$ROOT_DIR/scripts/lib/config_env.sh"
load_config_env

echo "waiting for Redpanda..."
until docker compose exec -T redpanda rpk cluster info >/dev/null 2>&1; do
  sleep 2
done

echo "waiting for Flink JobManager..."
until curl -fsS "http://localhost:${HOST_FLINK_PORT:-8081}/overview" >/dev/null 2>&1; do
  sleep 2
done

echo "infrastructure ready"
