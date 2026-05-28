#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

. "$ROOT_DIR/scripts/lib/port_state.sh"
load_saved_ports

QUESTDB_HTTP_PORT="${HOST_QUESTDB_HTTP_PORT:-9000}"
QUESTDB_ILP_PORT="${HOST_QUESTDB_ILP_PORT:-9009}"
QUESTDB_EXEC_URL="http://127.0.0.1:${QUESTDB_HTTP_PORT}/exec"

echo "waiting for QuestDB HTTP API..."
until curl -fsSG "$QUESTDB_EXEC_URL" --data-urlencode "query=SELECT 1" >/dev/null 2>&1; do
  sleep 2
done

echo "waiting for QuestDB ILP port..."
until python3 - <<'PY'
import os
import socket
import sys

port = int(os.environ.get("HOST_QUESTDB_ILP_PORT", "9009"))
sock = socket.socket()
sock.settimeout(1)
try:
    sock.connect(("127.0.0.1", port))
except OSError:
    sys.exit(1)
finally:
    sock.close()
PY
do
  sleep 2
done

echo "questdb ready"
