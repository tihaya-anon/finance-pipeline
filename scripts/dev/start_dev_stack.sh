#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

. "$ROOT_DIR/scripts/lib/port_state.sh"

mkdir -p artifacts
SERVICE_PID_FILE="$ROOT_DIR/artifacts/service-pids.env"

start_background_service() {
  local name="$1"
  local log_file="$2"
  shift 2

  setsid env PYTHONUNBUFFERED=1 "$@" > "$log_file" 2>&1 &
  local pid=$!
  sleep 1

  if ! kill -0 "$pid" >/dev/null 2>&1; then
    echo "Failed to start $name. Last log lines:" >&2
    tail -n 50 "$log_file" >&2 || true
    exit 1
  fi

  STARTED_SERVICE_PID="$pid"
}

cleanup_partial_compose_state
resolve_runtime_ports
save_runtime_ports

uv --directory app sync --group dev
docker compose up -d --build redpanda redpanda-console questdb grafana jobmanager taskmanager
./scripts/infra/wait_for_infra.sh
./scripts/infra/wait_for_questdb.sh
./scripts/infra/init_questdb_schema.sh
./scripts/infra/create_topics.sh

docker compose exec -T jobmanager /bin/bash -lc "/opt/flink/bin/sql-client.sh -f /opt/flink/sql/market_features.sql" \
  > artifacts/flink-submit.log 2>&1 || true

./scripts/infra/apply_topic_retention.sh "${DEV_TOPIC_RETENTION_MS}"

pkill -f "scripts/python/strategy_service.py --max-messages 0" >/dev/null 2>&1 || true
pkill -f "scripts/python/portfolio_service.py --max-messages 0" >/dev/null 2>&1 || true
pkill -f "scripts/python/questdb_sink.py --max-messages 0" >/dev/null 2>&1 || true

start_background_service strategy-service artifacts/strategy.log \
  uv --directory app run python "$ROOT_DIR/scripts/python/strategy_service.py" --max-messages 0
STRATEGY_PID="$STARTED_SERVICE_PID"

start_background_service portfolio-service artifacts/portfolio.log \
  uv --directory app run python "$ROOT_DIR/scripts/python/portfolio_service.py" --max-messages 0
PORTFOLIO_PID="$STARTED_SERVICE_PID"

start_background_service questdb-sink artifacts/questdb-sink.log \
  uv --directory app run python "$ROOT_DIR/scripts/python/questdb_sink.py" --max-messages 0 --port "${HOST_QUESTDB_ILP_PORT}"
QUESTDB_SINK_PID="$STARTED_SERVICE_PID"

cat > "$SERVICE_PID_FILE" <<EOF
STRATEGY_PID=$STRATEGY_PID
PORTFOLIO_PID=$PORTFOLIO_PID
QUESTDB_SINK_PID=$QUESTDB_SINK_PID
EOF

echo "Dev stack is ready."
echo "Kafka bootstrap: ${KAFKA_BOOTSTRAP_SERVERS}"
echo "Redpanda Console: http://127.0.0.1:${HOST_CONSOLE_PORT}"
echo "Grafana: http://127.0.0.1:${HOST_GRAFANA_PORT}"
echo "QuestDB Web Console: http://127.0.0.1:${HOST_QUESTDB_HTTP_PORT}"
echo "Replay sample data with: uv --directory app run python scripts/python/replay_market.py --speedup 50"
echo "Stream live Binance data with: uv --directory app run python scripts/python/stream_binance.py"
