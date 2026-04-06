#!/usr/bin/env bash
set -euo pipefail

until python3 - <<'PY'
import socket
sock = socket.socket()
sock.settimeout(1)
try:
    sock.connect(("127.0.0.1", int(__import__("os").environ.get("HOST_QUESTDB_ILP_PORT", "9009"))))
finally:
    sock.close()
PY
do
  sleep 2
done

echo "questdb ready"
