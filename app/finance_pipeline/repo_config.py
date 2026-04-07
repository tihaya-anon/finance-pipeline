from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
from typing import Any

import yaml


PACKAGE_ROOT = Path(__file__).resolve().parent
APP_ROOT = PACKAGE_ROOT.parent
REPO_ROOT = APP_ROOT.parent
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "development.yaml"

CONFIG_ENV_MAPPINGS = {
    "ports.kafka": "HOST_KAFKA_PORT",
    "ports.redpanda_admin": "HOST_REDPANDA_ADMIN_PORT",
    "ports.console": "HOST_CONSOLE_PORT",
    "ports.grafana": "HOST_GRAFANA_PORT",
    "ports.flink": "HOST_FLINK_PORT",
    "ports.questdb_http": "HOST_QUESTDB_HTTP_PORT",
    "ports.questdb_ilp": "HOST_QUESTDB_ILP_PORT",
    "ports.questdb_pg": "HOST_QUESTDB_PG_PORT",
    "retention.topic_retention_ms": "DEV_TOPIC_RETENTION_MS",
    "retention.questdb_ttl": "DEV_QUESTDB_TTL",
    "sources.replay.speedup": "REPLAY_SPEEDUP",
    "sources.replay.fast_speedup": "REPLAY_FAST_SPEEDUP",
    "sources.replay.fixture_csv": "REPLAY_FIXTURE_CSV",
    "sources.binance.stream_url": "BINANCE_STREAM_URL",
    "sources.onchain.ws_url": "EVM_WS_URL",
    "sources.onchain.http_url": "EVM_HTTP_URL",
    "sources.onchain.pair_address": "EVM_PAIR_ADDRESS",
    "sources.onchain.base_symbol": "EVM_BASE_SYMBOL",
    "sources.onchain.quote_symbol": "EVM_QUOTE_SYMBOL",
    "sources.onchain.base_decimals": "EVM_BASE_DECIMALS",
    "sources.onchain.quote_decimals": "EVM_QUOTE_DECIMALS",
    "sources.onchain.capture_output": "ONCHAIN_CAPTURE_OUTPUT",
    "sources.onchain.capture_max_events": "ONCHAIN_CAPTURE_MAX_EVENTS",
    "sources.synthetic.output_csv": "SYNTHETIC_OUTPUT_CSV",
    "sources.synthetic.symbol": "SYNTHETIC_SYMBOL",
    "sources.synthetic.start_time": "SYNTHETIC_START_TIME",
    "sources.synthetic.start_price": "SYNTHETIC_START_PRICE",
    "sources.synthetic.tick_count": "SYNTHETIC_TICK_COUNT",
    "sources.synthetic.interval_ms": "SYNTHETIC_INTERVAL_MS",
    "sources.synthetic.quantity_min": "SYNTHETIC_QUANTITY_MIN",
    "sources.synthetic.quantity_max": "SYNTHETIC_QUANTITY_MAX",
    "sources.synthetic.volatility_bps": "SYNTHETIC_VOLATILITY_BPS",
    "sources.synthetic.drift_bps": "SYNTHETIC_DRIFT_BPS",
    "sources.synthetic.seed": "SYNTHETIC_SEED",
}


def resolve_config_path(config_path: str | None = None) -> Path:
    configured_path = config_path or os.getenv("FINANCE_PIPELINE_CONFIG")
    if not configured_path:
        return DEFAULT_CONFIG_PATH

    path = Path(configured_path)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def load_repo_config(config_path: str | None = None) -> dict[str, Any]:
    path = resolve_config_path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}

    if not isinstance(loaded, dict):
        raise ValueError(f"Config file must contain a YAML mapping: {path}")
    return loaded


def get_config_value(config: dict[str, Any], dotted_path: str, default: Any = None) -> Any:
    current: Any = config
    for segment in dotted_path.split("."):
        if not isinstance(current, dict) or segment not in current:
            return default
        current = current[segment]
    return current


def resolve_repo_path(raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def build_config_env(config_path: str | None = None) -> dict[str, str]:
    config = load_repo_config(config_path)
    env_values = {
        "FINANCE_PIPELINE_CONFIG": str(resolve_config_path(config_path)),
    }

    for dotted_path, env_name in CONFIG_ENV_MAPPINGS.items():
        value = get_config_value(config, dotted_path)
        if value is None:
            continue
        if dotted_path.endswith("_csv") or dotted_path.endswith("_output"):
            value = str(resolve_repo_path(str(value)))
        env_values[env_name] = str(value)

    host_kafka_port = env_values.get("HOST_KAFKA_PORT", "39092")
    env_values["KAFKA_BOOTSTRAP_SERVERS"] = f"localhost:{host_kafka_port}"
    return env_values


def format_shell_exports(config_path: str | None = None) -> str:
    env_values = build_config_env(config_path)
    return "\n".join(f"export {key}={shlex.quote(value)}" for key, value in sorted(env_values.items()))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render repository config into shell-friendly env exports.")
    parser.add_argument("--config", default=os.getenv("FINANCE_PIPELINE_CONFIG"))
    parser.add_argument("--format", choices=["shell", "json"], default="shell")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.format == "json":
        print(json.dumps(build_config_env(args.config), indent=2, sort_keys=True))
        return
    print(format_shell_exports(args.config))


if __name__ == "__main__":
    main()
