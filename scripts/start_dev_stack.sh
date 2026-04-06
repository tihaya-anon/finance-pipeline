#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p artifacts

uv --directory app sync --group dev
docker compose up -d --build redpanda redpanda-console questdb grafana jobmanager taskmanager
./scripts/wait_for_infra.sh
./scripts/create_topics.sh

docker compose exec -T jobmanager /bin/bash -lc "/opt/flink/bin/sql-client.sh -f /opt/flink/sql/market_features.sql" \
  > artifacts/flink-submit.log 2>&1 || true

./scripts/apply_topic_retention.sh 86400000

pkill -f "uv --directory app run strategy-service --max-messages 0" >/dev/null 2>&1 || true
pkill -f "uv --directory app run portfolio-service --max-messages 0" >/dev/null 2>&1 || true
pkill -f "uv --directory app run questdb-sink --max-messages 0" >/dev/null 2>&1 || true

nohup uv --directory app run strategy-service --max-messages 0 > artifacts/strategy.log 2>&1 &
nohup uv --directory app run portfolio-service --max-messages 0 > artifacts/portfolio.log 2>&1 &
nohup uv --directory app run questdb-sink --max-messages 0 > artifacts/questdb-sink.log 2>&1 &

echo "Dev stack is ready."
echo "Redpanda Console: http://127.0.0.1:8080"
echo "Grafana: http://127.0.0.1:3000"
echo "QuestDB Web Console: http://127.0.0.1:9000"
echo "Replay sample data with: uv --directory app run replay-market --speedup 50"
echo "Stream live Binance data with: uv --directory app run stream-binance"
