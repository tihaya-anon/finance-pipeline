#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

. "$ROOT_DIR/scripts/lib/port_state.sh"
load_saved_ports

QUESTDB_HTTP_PORT="${HOST_QUESTDB_HTTP_PORT:-9000}"
QUESTDB_EXEC_URL="http://127.0.0.1:${QUESTDB_HTTP_PORT}/exec"
QUESTDB_TTL="${DEV_QUESTDB_TTL:-6 HOURS}"

run_query() {
  local query="$1"
  local response=""

  response="$(curl -fsSG "$QUESTDB_EXEC_URL" --data-urlencode "query=$query")"
  if grep -q '"error"' <<<"$response"; then
    echo "QuestDB schema init failed: $response" >&2
    return 1
  fi
}

run_query "DROP TABLE IF EXISTS market_features"
run_query "DROP TABLE IF EXISTS trade_signals"
run_query "DROP TABLE IF EXISTS portfolio_snapshots"

run_query "CREATE TABLE market_features (
  timestamp TIMESTAMP,
  symbol SYMBOL,
  venue SYMBOL,
  instrument_type SYMBOL,
  base_asset SYMBOL,
  quote_asset SYMBOL,
  window_start VARCHAR,
  window_end VARCHAR,
  trade_count LONG,
  avg_price DOUBLE,
  vwap DOUBLE,
  high_price DOUBLE,
  low_price DOUBLE,
  open_price DOUBLE,
  close_price DOUBLE,
  high_low_range DOUBLE,
  total_quantity DOUBLE,
  notional_volume DOUBLE,
  buy_quantity DOUBLE,
  sell_quantity DOUBLE,
  volume_imbalance DOUBLE,
  price_volatility DOUBLE,
  price_return DOUBLE
) TIMESTAMP(timestamp) PARTITION BY HOUR TTL ${QUESTDB_TTL} WAL"

run_query "CREATE TABLE trade_signals (
  timestamp TIMESTAMP,
  symbol SYMBOL,
  venue SYMBOL,
  instrument_type SYMBOL,
  base_asset SYMBOL,
  quote_asset SYMBOL,
  generated_at VARCHAR,
  window_end VARCHAR,
  target_position LONG,
  target_position_size DOUBLE,
  reference_price DOUBLE,
  price_return DOUBLE,
  reason VARCHAR
) TIMESTAMP(timestamp) PARTITION BY HOUR TTL ${QUESTDB_TTL} WAL"

run_query "CREATE TABLE portfolio_snapshots (
  timestamp TIMESTAMP,
  symbol SYMBOL,
  venue SYMBOL,
  instrument_type SYMBOL,
  base_asset SYMBOL,
  quote_asset SYMBOL,
  event_timestamp VARCHAR,
  action VARCHAR,
  fill_price DOUBLE,
  target_position LONG,
  current_position LONG,
  target_position_size DOUBLE,
  current_position_size DOUBLE,
  cash DOUBLE,
  equity DOUBLE
) TIMESTAMP(timestamp) PARTITION BY HOUR TTL ${QUESTDB_TTL} WAL"

echo "QuestDB schema is ready."
