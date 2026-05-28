SHELL := /bin/bash

ROOT_DIR := $(CURDIR)
CONFIG_FILE ?= config/development.yaml
export FINANCE_PIPELINE_CONFIG := $(CONFIG_FILE)

CONFIG_ENV = . ./scripts/lib/config_env.sh && load_config_env

.PHONY: help install test mvp dev docker stop reset clean-data retention replay replay-fast binance onchain capture-onchain generate-synthetic replay-synthetic simulate vol-labels compose-config net config-show

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
	@echo "  make simulate      - continuously stream synthetic ticks using a YAML scenario"
	@echo "  make vol-labels    - generate offline future realized volatility labels from a tick CSV"
	@echo "  make binance       - stream live Binance aggTrade data"
	@echo "  make onchain       - stream EVM AMM swap logs into Kafka"
	@echo "  make capture-onchain - capture onchain swap logs into a local fixture"
	@echo "  make compose-config- print docker compose config with active ports"
	@echo "  make net           - show UI and data network interfaces"
	@echo ""
	@echo "Example:"
	@echo "  make dev CONFIG_FILE=config/development.yaml"
	@echo ""
	@echo "Most runtime defaults now come from $(CONFIG_FILE)."

config-show:
	@$(CONFIG_ENV) && uv --directory app run python "$(ROOT_DIR)/scripts/python/config_export.py" --config "$$FINANCE_PIPELINE_CONFIG" --format json

install:
	@$(CONFIG_ENV) && uv --directory app sync --group dev

test:
	@$(CONFIG_ENV) && uv --directory app run pytest

mvp:
	@$(CONFIG_ENV) && ./scripts/dev/run_mvp.sh

dev:
	@$(CONFIG_ENV) && ./scripts/dev/start_dev_stack.sh

docker: dev

stop:
	@$(CONFIG_ENV) && ./scripts/dev/stop_stack.sh

reset:
	@$(CONFIG_ENV) && ./scripts/dev/reset_stack.sh

clean-data:
	@$(CONFIG_ENV) && ./scripts/dev/reset_dev_data.sh

retention:
	@$(CONFIG_ENV) && ./scripts/infra/apply_topic_retention.sh "$${RETENTION_MS:-$$DEV_TOPIC_RETENTION_MS}"

replay:
	@$(CONFIG_ENV) && uv --directory app run python "$(ROOT_DIR)/scripts/python/replay_market.py" --shift-to-now

replay-fast:
	@$(CONFIG_ENV) && uv --directory app run python "$(ROOT_DIR)/scripts/python/replay_market.py" --shift-to-now --speedup "$$REPLAY_FAST_SPEEDUP"

generate-synthetic:
	@$(CONFIG_ENV) && uv --directory app run python "$(ROOT_DIR)/scripts/python/generate_synthetic_fixture.py"

replay-synthetic:
	@$(CONFIG_ENV) && uv --directory app run python "$(ROOT_DIR)/scripts/python/generate_synthetic_fixture.py" && uv --directory app run python "$(ROOT_DIR)/scripts/python/replay_market.py" --csv "$$SYNTHETIC_OUTPUT_CSV"

simulate:
	@$(CONFIG_ENV) && uv --directory app run python "$(ROOT_DIR)/scripts/python/stream_simulated.py"

vol-labels:
	@$(CONFIG_ENV) && uv --directory app run python "$(ROOT_DIR)/scripts/python/generate_vol_labels.py"

binance:
	@$(CONFIG_ENV) && uv --directory app run python "$(ROOT_DIR)/scripts/python/stream_binance.py"

onchain:
	@$(CONFIG_ENV) && uv --directory app run python "$(ROOT_DIR)/scripts/python/stream_onchain.py"

capture-onchain:
	@$(CONFIG_ENV) && uv --directory app run python "$(ROOT_DIR)/scripts/python/capture_onchain.py"

compose-config:
	@$(CONFIG_ENV) && docker compose config

net:
	@$(CONFIG_ENV) && . ./scripts/lib/port_state.sh && load_saved_ports && \
	echo "UI Interfaces:" && \
	echo "  Grafana:               http://127.0.0.1:$${HOST_GRAFANA_PORT}" && \
	echo "  Redpanda Console:      http://127.0.0.1:$${HOST_CONSOLE_PORT}" && \
	echo "  QuestDB Web Console:   http://127.0.0.1:$${HOST_QUESTDB_HTTP_PORT}" && \
	echo "  Flink Web UI:          http://127.0.0.1:$${HOST_FLINK_PORT}" && \
	echo "" && \
	echo "Data Interfaces:" && \
	echo "  Kafka Bootstrap:       $${KAFKA_BOOTSTRAP_SERVERS}" && \
	echo "  Redpanda Admin API:    http://127.0.0.1:$${HOST_REDPANDA_ADMIN_PORT}" && \
	echo "  QuestDB HTTP API:      http://127.0.0.1:$${HOST_QUESTDB_HTTP_PORT}/exec" && \
	echo "  QuestDB ILP TCP:       127.0.0.1:$${HOST_QUESTDB_ILP_PORT}" && \
	echo "  QuestDB PGWire:        postgresql://admin:quest@127.0.0.1:$${HOST_QUESTDB_PG_PORT}/qdb" && \
	echo "" && \
	echo "Runtime Defaults:" && \
	echo "  Topic Retention:       $${DEV_TOPIC_RETENTION_MS} ms" && \
	echo "  QuestDB TTL:           $${DEV_QUESTDB_TTL}" && \
	echo "  Replay Fixture:        $${REPLAY_FIXTURE_CSV}" && \
	echo "  Synthetic Fixture:     $${SYNTHETIC_OUTPUT_CSV}" && \
	echo "  Simulation Scenario:   $${SIMULATION_SCENARIO}"
