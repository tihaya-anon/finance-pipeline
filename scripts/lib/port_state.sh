#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PORT_STATE_FILE="$ROOT_DIR/artifacts/ports.env"

. "$ROOT_DIR/scripts/lib/config_env.sh"

PORT_VARIABLES=(
  HOST_KAFKA_PORT
  HOST_REDPANDA_ADMIN_PORT
  HOST_CONSOLE_PORT
  HOST_GRAFANA_PORT
  HOST_FLINK_PORT
  HOST_QUESTDB_HTTP_PORT
  HOST_QUESTDB_ILP_PORT
  HOST_QUESTDB_PG_PORT
)

ASSIGNED_PORTS=()

default_port_for() {
  case "$1" in
    HOST_KAFKA_PORT) echo "${HOST_KAFKA_PORT:-39092}" ;;
    HOST_REDPANDA_ADMIN_PORT) echo "${HOST_REDPANDA_ADMIN_PORT:-9644}" ;;
    HOST_CONSOLE_PORT) echo "${HOST_CONSOLE_PORT:-8080}" ;;
    HOST_GRAFANA_PORT) echo "${HOST_GRAFANA_PORT:-3000}" ;;
    HOST_FLINK_PORT) echo "${HOST_FLINK_PORT:-8081}" ;;
    HOST_QUESTDB_HTTP_PORT) echo "${HOST_QUESTDB_HTTP_PORT:-9000}" ;;
    HOST_QUESTDB_ILP_PORT) echo "${HOST_QUESTDB_ILP_PORT:-9009}" ;;
    HOST_QUESTDB_PG_PORT) echo "${HOST_QUESTDB_PG_PORT:-8812}" ;;
    *)
      echo "Unknown port variable: $1" >&2
      return 1
      ;;
  esac
}

read_saved_port() {
  local name="$1"

  [[ -f "$PORT_STATE_FILE" ]] || return 1

  awk -F= -v key="$name" '$1 == key { value = $2 } END { if (value != "") print value; else exit 1 }' "$PORT_STATE_FILE"
}

can_bind_port() {
  local port="$1"

  python3 - "$port" <<'PY'
import socket
import sys

port = int(sys.argv[1])
sock = socket.socket()
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    sock.bind(("0.0.0.0", port))
except OSError:
    raise SystemExit(1)
finally:
    sock.close()
PY
}

is_port_already_assigned() {
  local port="$1"
  local assigned_port=""

  for assigned_port in "${ASSIGNED_PORTS[@]}"; do
    [[ "$assigned_port" == "$port" ]] && return 0
  done

  return 1
}

compose_has_partial_state() {
  local status=""

  for status in created exited dead restarting; do
    if docker compose ps -a --status "$status" --services 2>/dev/null | grep -q .; then
      return 0
    fi
  done

  return 1
}

cleanup_partial_compose_state() {
  compose_has_partial_state || return 0

  echo "Detected partial compose state; cleaning it before restart."
  docker compose down --remove-orphans >/dev/null 2>&1 || true
}

is_port_in_use() {
  local port="$1"
  ! can_bind_port "$port"
}

find_available_port() {
  local port="$1"

  while is_port_in_use "$port" || is_port_already_assigned "$port"; do
    ((port++))
  done

  echo "$port"
}

resolve_port_variable() {
  local name="$1"
  local preferred_port="${!name:-}"
  local saved_port=""
  local selected_port=""

  if [[ -z "$preferred_port" ]]; then
    saved_port="$(read_saved_port "$name" || true)"
    preferred_port="${saved_port:-$(default_port_for "$name")}"
  fi

  selected_port="$(find_available_port "$preferred_port")"
  if [[ "$selected_port" != "$preferred_port" ]]; then
    echo "Port $preferred_port for $name is busy; using $selected_port instead."
  fi

  printf -v "$name" "%s" "$selected_port"
  export "$name"
}

resolve_runtime_ports() {
  mkdir -p "$ROOT_DIR/artifacts"
  ASSIGNED_PORTS=()

  # Load non-port runtime config before resolving host port assignments.
  load_config_env

  for name in "${PORT_VARIABLES[@]}"; do
    resolve_port_variable "$name"
    ASSIGNED_PORTS+=("${!name}")
  done

  export KAFKA_BOOTSTRAP_SERVERS="${KAFKA_BOOTSTRAP_SERVERS:-localhost:${HOST_KAFKA_PORT}}"
}

save_runtime_ports() {
  mkdir -p "$ROOT_DIR/artifacts"

  {
    for name in "${PORT_VARIABLES[@]}"; do
      printf "%s=%s\n" "$name" "${!name}"
    done
  } > "$PORT_STATE_FILE"
}

load_saved_ports() {
  local saved_port=""

  [[ -f "$PORT_STATE_FILE" ]] || return 0

  for name in "${PORT_VARIABLES[@]}"; do
    [[ -n "${!name:-}" ]] && continue
    saved_port="$(read_saved_port "$name" || true)"
    [[ -n "$saved_port" ]] || continue
    printf -v "$name" "%s" "$saved_port"
    export "$name"
  done
  export KAFKA_BOOTSTRAP_SERVERS="${KAFKA_BOOTSTRAP_SERVERS:-localhost:${HOST_KAFKA_PORT}}"
}
