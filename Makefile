SHELL := /bin/bash

HOST_KAFKA_PORT ?= 39092
HOST_REDPANDA_ADMIN_PORT ?= 9644
HOST_CONSOLE_PORT ?= 8080
HOST_GRAFANA_PORT ?= 3000
HOST_FLINK_PORT ?= 8081
HOST_QUESTDB_HTTP_PORT ?= 9000
HOST_QUESTDB_ILP_PORT ?= 9009
HOST_QUESTDB_PG_PORT ?= 8812

export HOST_KAFKA_PORT
export HOST_REDPANDA_ADMIN_PORT
export HOST_CONSOLE_PORT
export HOST_GRAFANA_PORT
export HOST_FLINK_PORT
export HOST_QUESTDB_HTTP_PORT
export HOST_QUESTDB_ILP_PORT
export HOST_QUESTDB_PG_PORT

.PHONY: help install test mvp dev docker stop reset clean-data retention replay replay-fast binance compose-config ports

help:
	@echo "Targets:"
	@echo "  make install       - sync Python deps with uv"
	@echo "  make test          - run Python tests"
	@echo "  make mvp           - run the bounded MVP flow"
	@echo "  make dev           - start long-running dev stack"
	@echo "  make docker        - alias of make dev"
	@echo "  make stop          - stop docker + local background services"
	@echo "  make reset         - stop and fully reset stack state"
	@echo "  make clean-data    - clear topics/artifacts while keeping stack up"
	@echo "  make retention     - apply topic retention, set RETENTION_MS=..."
	@echo "  make replay        - replay sample data"
	@echo "  make replay-fast   - replay sample data faster"
	@echo "  make binance       - stream live Binance aggTrade data"
	@echo "  make compose-config- print docker compose config with active ports"
	@echo "  make ports         - show current host port mapping values"
	@echo ""
	@echo "Example:"
	@echo "  make dev HOST_QUESTDB_HTTP_PORT=19000 HOST_GRAFANA_PORT=13000"

install:
	uv --directory app sync --group dev

test:
	uv --directory app run pytest

mvp:
	./scripts/run_mvp.sh

dev:
	./scripts/start_dev_stack.sh

docker: dev

stop:
	./scripts/stop_stack.sh

reset:
	./scripts/reset_stack.sh

clean-data:
	./scripts/reset_dev_data.sh

retention:
	./scripts/apply_topic_retention.sh $${RETENTION_MS:-86400000}

replay:
	uv --directory app run replay-market --speedup 50

replay-fast:
	uv --directory app run replay-market --speedup 200

binance:
	uv --directory app run stream-binance

compose-config:
	docker compose config

ports:
	@echo "HOST_KAFKA_PORT=$(HOST_KAFKA_PORT)"
	@echo "HOST_REDPANDA_ADMIN_PORT=$(HOST_REDPANDA_ADMIN_PORT)"
	@echo "HOST_CONSOLE_PORT=$(HOST_CONSOLE_PORT)"
	@echo "HOST_GRAFANA_PORT=$(HOST_GRAFANA_PORT)"
	@echo "HOST_FLINK_PORT=$(HOST_FLINK_PORT)"
	@echo "HOST_QUESTDB_HTTP_PORT=$(HOST_QUESTDB_HTTP_PORT)"
	@echo "HOST_QUESTDB_ILP_PORT=$(HOST_QUESTDB_ILP_PORT)"
	@echo "HOST_QUESTDB_PG_PORT=$(HOST_QUESTDB_PG_PORT)"
