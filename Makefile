SHELL := /bin/bash

CONFIG_FILE ?= config/development.yaml
export FINANCE_PIPELINE_CONFIG := $(CONFIG_FILE)

CONFIG_ENV = . ./scripts/config_env.sh && load_config_env

.PHONY: help install test mvp dev docker stop reset clean-data retention replay replay-fast binance onchain capture-onchain generate-synthetic replay-synthetic compose-config ports config-show

help:
	@echo "Targets:"
	@echo "  make config-show   - print YAML-derived runtime config"
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
	@echo "  make generate-synthetic - generate a local synthetic CSV fixture"
	@echo "  make replay-synthetic   - generate then replay the synthetic fixture"
	@echo "  make binance       - stream live Binance aggTrade data"
	@echo "  make onchain       - stream EVM AMM swap logs into Kafka"
	@echo "  make capture-onchain - capture onchain swap logs into a local fixture"
	@echo "  make compose-config- print docker compose config with active ports"
	@echo "  make ports         - show current host port mapping values"
	@echo ""
	@echo "Example:"
	@echo "  make dev CONFIG_FILE=config/development.yaml"
	@echo ""
	@echo "Most runtime defaults now come from $(CONFIG_FILE)."

config-show:
	@$(CONFIG_ENV) && uv --directory app run config-export --config "$$FINANCE_PIPELINE_CONFIG" --format json

install:
	@$(CONFIG_ENV) && uv --directory app sync --group dev

test:
	@$(CONFIG_ENV) && uv --directory app run pytest

mvp:
	@$(CONFIG_ENV) && ./scripts/run_mvp.sh

dev:
	@$(CONFIG_ENV) && ./scripts/start_dev_stack.sh

docker: dev

stop:
	@$(CONFIG_ENV) && ./scripts/stop_stack.sh

reset:
	@$(CONFIG_ENV) && ./scripts/reset_stack.sh

clean-data:
	@$(CONFIG_ENV) && ./scripts/reset_dev_data.sh

retention:
	@$(CONFIG_ENV) && ./scripts/apply_topic_retention.sh "$${RETENTION_MS:-$$DEV_TOPIC_RETENTION_MS}"

replay:
	@$(CONFIG_ENV) && uv --directory app run replay-market

replay-fast:
	@$(CONFIG_ENV) && uv --directory app run replay-market --speedup "$$REPLAY_FAST_SPEEDUP"

generate-synthetic:
	@$(CONFIG_ENV) && uv --directory app run generate-synthetic-fixture

replay-synthetic:
	@$(CONFIG_ENV) && uv --directory app run generate-synthetic-fixture && uv --directory app run replay-market --csv "$$SYNTHETIC_OUTPUT_CSV"

binance:
	@$(CONFIG_ENV) && uv --directory app run stream-binance

onchain:
	@$(CONFIG_ENV) && uv --directory app run stream-onchain

capture-onchain:
	@$(CONFIG_ENV) && uv --directory app run capture-onchain

compose-config:
	@$(CONFIG_ENV) && docker compose config

ports:
	@$(CONFIG_ENV) && . ./scripts/port_state.sh && load_saved_ports && \
	echo "HOST_KAFKA_PORT=$${HOST_KAFKA_PORT}" && \
	echo "HOST_REDPANDA_ADMIN_PORT=$${HOST_REDPANDA_ADMIN_PORT}" && \
	echo "HOST_CONSOLE_PORT=$${HOST_CONSOLE_PORT}" && \
	echo "HOST_GRAFANA_PORT=$${HOST_GRAFANA_PORT}" && \
	echo "HOST_FLINK_PORT=$${HOST_FLINK_PORT}" && \
	echo "HOST_QUESTDB_HTTP_PORT=$${HOST_QUESTDB_HTTP_PORT}" && \
	echo "HOST_QUESTDB_ILP_PORT=$${HOST_QUESTDB_ILP_PORT}" && \
	echo "HOST_QUESTDB_PG_PORT=$${HOST_QUESTDB_PG_PORT}" && \
	echo "KAFKA_BOOTSTRAP_SERVERS=$${KAFKA_BOOTSTRAP_SERVERS}" && \
	echo "DEV_TOPIC_RETENTION_MS=$${DEV_TOPIC_RETENTION_MS}" && \
	echo "DEV_QUESTDB_TTL=$${DEV_QUESTDB_TTL}" && \
	echo "REPLAY_FIXTURE_CSV=$${REPLAY_FIXTURE_CSV}" && \
	echo "SYNTHETIC_OUTPUT_CSV=$${SYNTHETIC_OUTPUT_CSV}"
